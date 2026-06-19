"""
extraction_service.py

Reads the raw file from disk → extracts all text in one pass →
sends full text to LLM in a single call → parses JSON response →
inserts rows into extracted_requirements table.

No chunks. No embeddings. No RAG. No Qdrant. No pipeline dependencies.

Provider (EXTRACTION_PROVIDER in .env):
    gemini    — Gemini 2.5 Flash  (free, 1M ctx, 1500 req/day)  ← default
    groq      — llama-3.3-70b     (free, 128K ctx, 14400 req/day)
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.models.extracted_requirement import ExtractedRequirement

logger = logging.getLogger(__name__)


class RetryableExtractionError(Exception):
    """
    Raised for transient LLM errors (503 overloaded, 429 rate-limit, timeout).
    The Celery task catches this and schedules a retry instead of giving up.
    """
    pass

_TYPE_PREFIX: dict[str, str] = {
    "Functional":      "FR",
    "Non-Functional":  "NFR",
    "Technical":       "TR",
    "Security":        "SEC",
    "Integration":     "INT",
    "Compliance":      "CMP",
    "Infrastructure":  "INF",
    "Support":         "SUP",
}

_SYSTEM_PROMPT = """You are a requirements analyst. Extract every distinct software requirement from this RFP document.

Return ONLY a valid JSON array. No explanation. No markdown fences. No prose. Just the raw JSON array.

Each item must have exactly these fields:
{
  "name": "2-5 word label e.g. Role-Based Access Control",
  "req_type": "one of: Functional | Non-Functional | Technical | Security | Integration | Compliance | Infrastructure | Support",
  "description": "2-4 complete sentences describing exactly what is required",
  "priority": "one of: Must Have | Should Have | Nice to Have | Not Specified",
  "section": "the section heading this requirement appears under in the document",
  "page_number": integer (0 if unknown),
  "confidence": float 0.0-1.0 (1.0=explicitly stated, 0.8=clearly implied, 0.6=inferred)
}

What counts as a requirement: anything the system or vendor MUST, SHALL, SHOULD, or NEEDS TO do or support.
What to skip: company background text, section headings alone, glossary entries, evaluation scoring weights, submission format instructions, pricing table headers.

Return [] if no requirements are found.
"""


# ── Text extraction ───────────────────────────────────────────────────────────

def _read_pdf(path: Path) -> str:
    # pyrefly: ignore [missing-import]
    import pdfplumber
    pages: list[str] = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.find_tables()
            bboxes = [t.bbox for t in tables]

            table_lines: list[str] = []
            for t in tables:
                for row in (t.extract() or []):
                    cells = [str(c).strip() if c else "" for c in row]
                    non_empty = [c for c in cells if c]
                    if non_empty:
                        table_lines.append(" | ".join(non_empty))

            prose_words: list[str] = []
            for w in page.extract_words():
                in_table = any(
                    bx0 - 2 <= w["x0"] and w["top"] >= by0 - 2
                    and w["x1"] <= bx1 + 2 and w["bottom"] <= by1 + 2
                    for bx0, by0, bx1, by1 in bboxes
                )
                if not in_table:
                    prose_words.append(w["text"])

            text = " ".join(prose_words)
            if table_lines:
                text += "\n\n" + "\n".join(table_lines)
            if text.strip():
                pages.append(f"[Page {i+1}]\n{text.strip()}")

    return "\n\n".join(pages)


def _read_docx(path: Path) -> str:
    # pyrefly: ignore [missing-import]
    from docx import Document as DocxDoc
    doc = DocxDoc(path)
    return "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())


def _read_xlsx(path: Path) -> str:
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheets: list[str] = []
    for sheet in wb.worksheets:
        rows = []
        for row in sheet.iter_rows(values_only=True):
            cells = [str(c).strip() if c is not None else "" for c in row]
            non_empty = [c for c in cells if c]
            if non_empty:
                rows.append(" | ".join(non_empty))
        if rows:
            sheets.append(f"[Sheet: {sheet.title}]\n" + "\n".join(rows))
    wb.close()
    return "\n\n".join(sheets)


def _extract_text(path: Path, file_type: str) -> str:
    ft = file_type.lower().strip(".")
    if ft == "pdf":
        return _read_pdf(path)
    elif ft in ("docx", "doc"):
        return _read_docx(path)
    elif ft in ("xlsx", "xls"):
        return _read_xlsx(path)
    raise ValueError(f"Unsupported file type: {file_type}")


# ── LLM calls ─────────────────────────────────────────────────────────────────

# Models tried in order. If the first is overloaded (503) the next is used.
# gemini-2.0-flash was discontinued June 1 2026 — replaced by gemini-2.5-flash-lite.
_GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]


def _call_gemini(text: str) -> str:
    from google import genai
    # pyrefly: ignore [missing-import]
    from google.genai import types as genai_types
    # pyrefly: ignore [missing-import]
    from google.genai import errors as genai_errors

    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY not set in .env")

    # Gemini 1M-token limit ≈ 3M chars; truncate defensively to avoid OOM/timeout
    MAX_CHARS = 2_800_000
    if len(text) > MAX_CHARS:
        logger.warning("ExtractionService: truncating to %d chars for Gemini 1M limit", MAX_CHARS)
        text = text[:MAX_CHARS]

    client = genai.Client(api_key=settings.gemini_api_key)
    last_exc: Exception | None = None

    for model_name in _GEMINI_MODELS:
        try:
            logger.info("ExtractionService: calling Gemini model=%s", model_name)
            response = client.models.generate_content(
                model=model_name,
                contents=f"Extract all requirements from this RFP:\n\n{text}",
                config=genai_types.GenerateContentConfig(
                    system_instruction=_SYSTEM_PROMPT,
                    temperature=0.1,
                ),
            )
            return response.text
        except genai_errors.ServerError as exc:
            # 503 = overloaded, try next model
            logger.warning(
                "ExtractionService: model=%s returned %s — trying next model",
                model_name, exc,
            )
            last_exc = exc
        except genai_errors.ClientError as exc:
            # 429 = rate limit — retryable but no point trying next model
            logger.warning("ExtractionService: rate-limited on model=%s: %s", model_name, exc)
            last_exc = exc
            break  # don't try other models, let Celery retry after backoff

    # All models failed — raise RetryableExtractionError so Celery retries
    raise RetryableExtractionError(f"All Gemini models unavailable: {last_exc}") from last_exc


def _call_groq(text: str) -> str:
    # pyrefly: ignore [missing-import]
    from groq import Groq
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY not set in .env")
    if len(text) > 380_000:
        logger.warning("ExtractionService: truncating to 380K chars for Groq 128K limit")
        text = text[:380_000]
    client = Groq(api_key=settings.groq_api_key)
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract all requirements from this RFP:\n\n{text}"},
        ],
        max_tokens=8000,
        temperature=0.1,
    )
    return resp.choices[0].message.content


def _call_llm(text: str) -> str:
    provider = settings.extraction_provider.lower()
    if provider == "gemini":
        return _call_gemini(text)
    elif provider == "groq":
        return _call_groq(text)
    raise ValueError(f"Unknown EXTRACTION_PROVIDER='{provider}'. Use: gemini | groq")


# ── Response parser ───────────────────────────────────────────────────────────

def _parse_json(raw: str) -> list[dict]:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            for v in parsed.values():
                if isinstance(v, list):
                    return v
        return []
    except json.JSONDecodeError:
        m = re.search(r"\[.*\]", raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
    logger.error("ExtractionService: could not parse LLM response as JSON. First 500 chars: %s", raw[:500])
    return []


# ── Dedup ─────────────────────────────────────────────────────────────────────

def _deduplicate(reqs: list[dict]) -> list[dict]:
    seen: list[dict] = []
    for req in reqs:
        tokens = set(req.get("description", "").lower().split())
        if len(tokens) < 5:
            seen.append(req)
            continue
        dup = any(
            len(tokens & set(ex.get("description", "").lower().split())) /
            max(len(tokens | set(ex.get("description", "").lower().split())), 1) >= 0.85
            for ex in seen
        )
        if not dup:
            seen.append(req)
    return seen


# ── Main service ──────────────────────────────────────────────────────────────

class ExtractionService:
    """
    Read file from disk → extract text → single LLM call → save to DB.
    That is all this does.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def run(self, document_id: str, project_id: str) -> None:
        logger.info(
            "ExtractionService.run: document=%s provider=%s",
            document_id, settings.extraction_provider,
        )

        # 1. Validate UUIDs
        try:
            doc_uuid = uuid.UUID(document_id)
            proj_uuid = uuid.UUID(project_id)
        except ValueError:
            # Can't load the document without a valid UUID — nothing to mark
            logger.error("ExtractionService: invalid UUIDs %s / %s", document_id, project_id)
            return

        # 2. Load document row
        document = self.db.get(Document, doc_uuid)
        if not document:
            # Document row missing — nothing to mark
            logger.error("ExtractionService: document %s not found", document_id)
            return

        # 3. Resolve file path
        file_path = Path(settings.upload_storage_root) / document.stored_path
        if not file_path.exists():
            logger.error("ExtractionService: file not on disk: %s", file_path)
            self._mark_extraction_failed(document, f"Uploaded file is missing from storage: {file_path.name}. Please re-upload the document.")
            return

        logger.info(
            "ExtractionService: reading %s (%s, %d bytes)",
            file_path.name, document.file_type, document.file_size_bytes,
        )

        # 4. Extract full text from file
        try:
            full_text = _extract_text(file_path, document.file_type)
        except Exception as exc:
            logger.error("ExtractionService: text extraction failed: %s", exc)
            self._mark_extraction_failed(document, f"Could not read text from document: {exc}")
            return

        if not full_text.strip():
            logger.error("ExtractionService: empty text from %s", document_id)
            self._mark_extraction_failed(document, "The document appears to be empty or contains no extractable text. Ensure the file is not password-protected or image-only.")
            return

        logger.info("ExtractionService: %d chars extracted", len(full_text))

        # 5. Single LLM call
        try:
            raw = _call_llm(full_text)
        except RetryableExtractionError:
            # Transient error (503 overloaded, 429 rate-limit, timeout).
            # Re-raise so the Celery task can schedule a retry.
            # Do NOT mark extraction_failed — it might succeed on the next attempt.
            logger.warning(
                "ExtractionService: transient LLM error for document=%s — will retry",
                document_id,
            )
            raise
        except Exception as exc:
            error_msg = str(exc)
            # Permanent error (bad API key, unsupported model, etc.) — log full
            # traceback and mark the document so the UI shows an error.
            logger.exception(
                "ExtractionService: permanent LLM failure for document=%s provider=%s — %s",
                document_id, settings.extraction_provider, error_msg,
            )
            self._mark_extraction_failed(document, error_msg)
            return

        # 6. Parse JSON
        reqs = _parse_json(raw)
        if not reqs:
            logger.warning("ExtractionService: LLM returned 0 requirements for %s", document_id)
            self._mark_extraction_failed(document, "The AI could not identify any requirements in this document. The file may not be an RFP, or its content may be structured in a format the AI cannot parse.")
            return

        logger.info("ExtractionService: %d requirements from LLM", len(reqs))

        # 7. Deduplicate
        reqs = _deduplicate(reqs)
        logger.info("ExtractionService: %d after dedup", len(reqs))

        # 8. Clear previous extraction for this document
        try:
            self.db.query(ExtractedRequirement).filter(
                ExtractedRequirement.document_id == doc_uuid
            ).delete(synchronize_session=False)
        except Exception as exc:
            self.db.rollback()
            logger.error("ExtractionService: failed to clear old rows: %s", exc)
            self._mark_extraction_failed(document, f"Database error while clearing previous results: {exc}")
            return

        # 9. Build and insert rows
        counters: dict[str, int] = {}
        rows: list[ExtractedRequirement] = []

        for req in reqs:
            req_type = str(req.get("req_type", "Functional"))
            prefix = _TYPE_PREFIX.get(req_type, "FR")
            counters[prefix] = counters.get(prefix, 0) + 1
            req_id = f"{prefix}-{counters[prefix]:02d}"

            rows.append(ExtractedRequirement(
                document_id=doc_uuid,
                project_id=proj_uuid,
                req_id=req_id,
                name=str(req.get("name", "Unnamed"))[:255],
                req_type=req_type[:64],
                description=str(req.get("description", "")),
                priority=str(req.get("priority", "Not Specified"))[:64],
                section=str(req.get("section", ""))[:512],
                page_number=int(req.get("page_number") or 0),
                confidence=float(req.get("confidence") or 1.0),
            ))

        try:
            self.db.add_all(rows)
            self.db.commit()
            logger.info(
                "ExtractionService: saved %d requirements for document=%s",
                len(rows), document_id,
            )
        except Exception as exc:
            self.db.rollback()
            logger.error("ExtractionService: DB insert failed: %s", exc)
            self._mark_extraction_failed(document, f"Database error while saving requirements: {exc}")
            return

        # 10. Mark document as fully extracted
        try:
            document.upload_status = "extracted"
            self.db.commit()
            logger.info(
                "ExtractionService: document=%s marked as extracted",
                document_id,
            )
        except Exception as exc:
            self.db.rollback()
            logger.error("ExtractionService: failed to mark document as extracted: %s", exc)

    def _mark_extraction_failed(self, document: Document, error_msg: str) -> None:
        """Persist extraction_failed status and the error message to the document row."""
        # Classify the error for a cleaner UI message
        msg = str(error_msg)
        if "429" in msg or "quota" in msg.lower() or "rate" in msg.lower():
            friendly = (
                f"LLM quota exceeded ({settings.extraction_provider.upper()}). "
                "The API key has hit its rate or daily limit. "
                "Switch EXTRACTION_PROVIDER or use a different API key."
            )
        elif "api_key" in msg.lower() or "api key" in msg.lower() or "invalid" in msg.lower():
            friendly = (
                f"Invalid API key for {settings.extraction_provider.upper()}. "
                "Check your key in .env and restart the worker."
            )
        elif "timeout" in msg.lower():
            friendly = "LLM request timed out. The document may be too large. Try again or switch provider."
        else:
            friendly = f"LLM extraction failed: {msg[:300]}"

        document.upload_status = "extraction_failed"
        document.extraction_error = friendly
        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.error("ExtractionService: could not save extraction_failed status: %s", exc)
