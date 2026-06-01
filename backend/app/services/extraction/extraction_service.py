"""
extraction_service.py — LLM-powered requirement extraction service.

Architecture decision:
    This service runs INSTEAD of the chunking → semantic chunking → classification
    pipeline for the "extraction" flow.  The existing chunking pipeline remains
    completely untouched and still runs for embedding / RAG retrieval.

    This service adds a PARALLEL fast path:
        parse (existing) → ExtractionService.run() → extracted_requirements table

    Flow triggered by:
        extraction_tasks.extract_requirements_task.delay(document_id, project_id)

    Provider strategy (configured via EXTRACTION_PROVIDER in .env):
        "gemini"   — Google Gemini 2.0 Flash (free: 1500 req/day, 1M context)
        "groq"     — Groq llama-3.3-70b (free: 14400 req/day)
        "anthropic" — Claude Sonnet (paid, highest quality)

    All providers use the same system prompt and return the same JSON schema.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.models.extracted_requirement import ExtractedRequirement

logger = logging.getLogger(__name__)

# ── Requirement type → ID prefix mapping ────────────────────────────────────
_TYPE_PREFIX: dict[str, str] = {
    "Functional": "FR",
    "Non-Functional": "NFR",
    "Technical": "TR",
    "Security": "SEC",
    "Integration": "INT",
    "Compliance": "CMP",
    "Infrastructure": "INF",
    "Support": "SUP",
}

# ── Extraction system prompt (shared across all providers) ───────────────────
_SYSTEM_PROMPT = """You are a requirements analyst specialising in extracting structured software \
requirements from RFP (Request for Proposal) documents.

Your task: extract every distinct requirement from the provided document and return them \
as a JSON array.

EXTRACTION RULES:
- Extract EVERY specific, actionable requirement — functional, non-functional, technical, \
security, integration, compliance, infrastructure, support.
- Each requirement must be a single self-contained statement.
- Do NOT extract: section titles, company background, evaluation criteria weights, \
pricing instructions, glossary entries, or submission format instructions.
- A requirement is something the SYSTEM or VENDOR must DO or SUPPORT — identifiable by \
modal verbs: must, shall, should, support, provide, enable, implement, ensure, handle, \
track, manage, integrate, maintain, allow, restrict, generate, notify.
- Merge related bullet points under the same feature into ONE requirement when they \
describe the same capability.
- For tables: extract each row as a separate requirement with full context from the \
header row.
- Keep descriptions concise but complete (2-4 sentences). Never truncate mid-sentence.

OUTPUT SCHEMA (return ONLY a valid JSON array, no prose, no markdown fences):
[
  {
    "name": "<2-5 word label, e.g. JWT Token Management>",
    "req_type": "<exactly one of: Functional | Non-Functional | Technical | Security | Integration | Compliance | Infrastructure | Support>",
    "description": "<complete 2-4 sentence description>",
    "priority": "<exactly one of: Must Have | Should Have | Nice to Have | Not Specified>",
    "section": "<source section heading from document>",
    "page_number": <integer, 0 if unknown>,
    "confidence": <float 0.0-1.0: 1.0=explicit, 0.8=implied, 0.6=inferred>
  }
]

If no requirements are found, return [].
"""


# ── Table-aware PDF page extractor ──────────────────────────────────────────

def _extract_pages_pdf(file_path: Path) -> list[dict]:
    """
    Extract pages from PDF using pdfplumber with table-aware handling.
    Tables are serialised as '| col1 | col2 |' rows, not raw merged text.
    Returns list of {page: int, text: str}.
    """
    try:
        import pdfplumber  # optional dep — only needed for PDF extraction path
    except ImportError:
        raise RuntimeError(
            "pdfplumber is required for PDF extraction. "
            "Add 'pdfplumber==0.11.4' to requirements.txt."
        )

    pages: list[dict] = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.find_tables()
            table_bboxes = [t.bbox for t in tables]

            # Serialise tables as labelled rows
            table_blocks: list[str] = []
            for table in tables:
                rows = table.extract()
                if not rows:
                    continue
                serialised_rows = []
                for row in rows:
                    cells = [str(c).strip() if c else "" for c in row]
                    non_empty = [c for c in cells if c]
                    if non_empty:
                        serialised_rows.append(" | ".join(non_empty))
                if serialised_rows:
                    table_blocks.append("\n".join(serialised_rows))

            # Extract prose that falls outside table bounding boxes
            words = page.extract_words()
            prose_words: list[str] = []
            for word in words:
                wx0, wy0, wx1, wy1 = (
                    word["x0"], word["top"], word["x1"], word["bottom"]
                )
                in_table = any(
                    bx0 - 2 <= wx0
                    and wy0 >= by0 - 2
                    and wx1 <= bx1 + 2
                    and wy1 <= by1 + 2
                    for bx0, by0, bx1, by1 in table_bboxes
                )
                if not in_table:
                    prose_words.append(word["text"])

            prose = " ".join(prose_words)
            full_text = prose
            if table_blocks:
                full_text += "\n\n[TABLE]\n" + "\n\n[TABLE]\n".join(table_blocks)

            if full_text.strip():
                pages.append({"page": i + 1, "text": full_text.strip()})

    return pages


def _extract_pages_from_parsed_content(parsed_content: list[dict]) -> list[dict]:
    """
    Convert already-parsed document content (stored in Document.parsed_content)
    into the page-list format expected by the extractor.

    parsed_content is a list of ParsedPage.to_dict() outputs:
        {"page_number": int, "text": str, "metadata": {...}}
    """
    pages: list[dict] = []
    for page_dict in parsed_content:
        text = page_dict.get("text", "").strip()
        if text:
            pages.append({
                "page": page_dict.get("page_number", 0),
                "text": text,
            })
    return pages


def _build_segments(
    pages: list[dict],
    window_size: int = 5,
    overlap: int = 1,
) -> list[dict]:
    """
    Group pages into overlapping windows so requirements that span page
    boundaries appear in at least one segment.

    Returns list of {start_page, end_page, text}.
    """
    segments: list[dict] = []
    n = len(pages)
    step = window_size - overlap
    i = 0
    while i < n:
        window = pages[i: i + window_size]
        combined = "\n\n---PAGE BREAK---\n\n".join(
            f"[Page {p['page']}]\n{p['text']}" for p in window
        )
        segments.append({
            "start_page": window[0]["page"],
            "end_page": window[-1]["page"],
            "text": combined,
        })
        i += step
    return segments


# ── Provider call functions ──────────────────────────────────────────────────

def _call_gemini(segment_text: str) -> list[dict]:
    """Call Google Gemini 2.0 Flash. Free: 1500 req/day, 1M token context."""
    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError(
            "google-generativeai is required for Gemini provider. "
            "Add 'google-generativeai==0.8.3' to requirements.txt."
        )

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=_SYSTEM_PROMPT,
    )
    response = model.generate_content(
        f"Extract all requirements from this RFP segment:\n\n{segment_text}"
    )
    return _parse_llm_response(response.text)


def _call_groq(segment_text: str) -> list[dict]:
    """Call Groq llama-3.3-70b-versatile. Free: 14400 req/day."""
    try:
        from groq import Groq
    except ImportError:
        raise RuntimeError(
            "groq is required for Groq provider. "
            "Add 'groq==0.11.0' to requirements.txt."
        )

    client = Groq(api_key=settings.groq_api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Extract all requirements from this RFP segment "
                    f"and return ONLY a JSON array:\n\n{segment_text}"
                ),
            },
        ],
        max_tokens=4096,
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content
    # Groq json_object mode may wrap the array in a key
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
        # Unwrap first list value
        for v in parsed.values():
            if isinstance(v, list):
                return v
        return []
    except json.JSONDecodeError:
        return _parse_llm_response(raw)


def _call_anthropic(segment_text: str) -> list[dict]:
    """Call Claude Sonnet. Paid, highest quality."""
    try:
        import anthropic
    except ImportError:
        raise RuntimeError(
            "anthropic is required for Anthropic provider. "
            "Add 'anthropic==0.40.0' to requirements.txt."
        )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Extract all requirements from this RFP segment "
                    f"and return ONLY a JSON array:\n\n{segment_text}"
                ),
            }
        ],
    )
    return _parse_llm_response(message.content[0].text)


def _parse_llm_response(raw: str) -> list[dict]:
    """
    Parse a raw LLM text response into a list of requirement dicts.
    Handles markdown fences, partial responses, and malformed JSON.
    """
    raw = raw.strip()
    # Strip markdown code fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        # Attempt to extract just the JSON array portion
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    logger.warning("ExtractionService: failed to parse LLM response as JSON")
    return []


# ── Deduplicator ─────────────────────────────────────────────────────────────

def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _deduplicate(raw_reqs: list[dict], threshold: float = 0.82) -> list[dict]:
    """
    Remove near-duplicate requirements using token-level Jaccard similarity.
    O(n²) — acceptable for typical RFP sizes (< 200 requirements).
    """
    seen: list[dict] = []
    for req in raw_reqs:
        desc = _normalise(req.get("description", ""))
        new_tokens = set(desc.split())
        if len(new_tokens) < 4:
            seen.append(req)
            continue
        is_dup = False
        for ex in seen:
            ex_tokens = set(_normalise(ex.get("description", "")).split())
            if not ex_tokens:
                continue
            jaccard = len(new_tokens & ex_tokens) / len(new_tokens | ex_tokens)
            if jaccard >= threshold:
                is_dup = True
                break
        if not is_dup:
            seen.append(req)
    return seen


# ── Main service class ────────────────────────────────────────────────────────

class ExtractionService:
    """
    Extracts structured requirements from a parsed document using an LLM.

    Called by the Celery task extraction_tasks.extract_requirements_task.
    Uses the document's already-parsed content (Document.parsed_content) so
    parsing does NOT run twice.

    The extraction provider is selected via settings.extraction_provider:
        "gemini"    — default (free, 1M context, best for large docs)
        "groq"      — free alternative
        "anthropic" — highest quality, paid

    This service does NOT modify any existing tables or services.
    It only writes to the `extracted_requirements` table.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def run(self, document_id: str, project_id: str) -> None:
        """
        Execute the full extraction pipeline for one document.

        Never raises — all errors are caught and logged.
        Writes results to the extracted_requirements table.

        Args:
            document_id: UUID string of the Document row.
            project_id:  UUID string of the owning Project.
        """
        logger.info(
            "ExtractionService.run: document=%s project=%s provider=%s",
            document_id,
            project_id,
            settings.extraction_provider,
        )

        # ── 1. Load document ─────────────────────────────────────
        try:
            doc_uuid = uuid.UUID(document_id)
            proj_uuid = uuid.UUID(project_id)
        except ValueError:
            logger.error("ExtractionService: invalid UUID(s): %s / %s", document_id, project_id)
            return

        document: Document | None = self.db.get(Document, doc_uuid)
        if document is None:
            logger.error("ExtractionService: document %s not found", document_id)
            return

        if not document.parsed_content:
            logger.error(
                "ExtractionService: document %s has no parsed_content — "
                "ensure parsing completed before extraction",
                document_id,
            )
            return

        # ── 2. Mark as extracting ─────────────────────────────────
        document.upload_status = "extracting"
        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.error("ExtractionService: failed to mark 'extracting': %s", exc)
            return

        # ── 3. Build page segments from parsed content ────────────
        try:
            pages = _extract_pages_from_parsed_content(document.parsed_content)
            if not pages:
                logger.warning(
                    "ExtractionService: no usable pages extracted from document %s",
                    document_id,
                )
                document.upload_status = "extraction_failed"
                self.db.commit()
                return

            segments = _build_segments(pages, window_size=5, overlap=1)
            logger.info(
                "ExtractionService: %d pages → %d segments for document=%s",
                len(pages),
                len(segments),
                document_id,
            )

            # ── 4. Call LLM on each segment ───────────────────────
            provider = settings.extraction_provider.lower()
            caller = {
                "gemini": _call_gemini,
                "groq": _call_groq,
                "anthropic": _call_anthropic,
            }.get(provider)

            if caller is None:
                raise ValueError(
                    f"Unknown extraction_provider '{provider}'. "
                    f"Must be one of: gemini, groq, anthropic."
                )

            all_raw: list[dict] = []
            for i, seg in enumerate(segments):
                logger.debug(
                    "ExtractionService: segment %d/%d pages=%d-%d",
                    i + 1,
                    len(segments),
                    seg["start_page"],
                    seg["end_page"],
                )
                try:
                    extracted = caller(seg["text"])
                    # Attach page hint to each extracted requirement
                    for req in extracted:
                        if not req.get("page_number"):
                            req["page_number"] = seg["start_page"]
                    all_raw.extend(extracted)
                    logger.debug(
                        "ExtractionService: segment %d → %d requirements", i + 1, len(extracted)
                    )
                except Exception as seg_exc:
                    logger.warning(
                        "ExtractionService: segment %d failed (%s) — skipping",
                        i + 1,
                        seg_exc,
                    )
                    continue

            # ── 5. Deduplicate ────────────────────────────────────
            unique_raw = _deduplicate(all_raw)
            logger.info(
                "ExtractionService: %d raw → %d after dedup for document=%s",
                len(all_raw),
                len(unique_raw),
                document_id,
            )

            # ── 6. Delete any previous extraction for this document ─
            self.db.query(ExtractedRequirement).filter(
                ExtractedRequirement.document_id == doc_uuid
            ).delete(synchronize_session=False)

            # ── 7. Assign IDs and bulk insert ─────────────────────
            counters: dict[str, int] = {}
            orm_rows: list[ExtractedRequirement] = []

            for req in unique_raw:
                req_type = req.get("req_type", "Functional")
                prefix = _TYPE_PREFIX.get(req_type, "FR")
                counters[prefix] = counters.get(prefix, 0) + 1
                req_id = f"{prefix}-{counters[prefix]:02d}"

                orm_rows.append(
                    ExtractedRequirement(
                        document_id=doc_uuid,
                        project_id=proj_uuid,
                        req_id=req_id,
                        name=req.get("name", "Unnamed Requirement")[:255],
                        req_type=req_type[:64],
                        description=req.get("description", ""),
                        priority=req.get("priority", "Not Specified")[:64],
                        section=req.get("section", "")[:512],
                        page_number=int(req.get("page_number", 0)),
                        confidence=float(req.get("confidence", 1.0)),
                    )
                )

            self.db.add_all(orm_rows)

            # ── 8. Mark completed ─────────────────────────────────
            document.upload_status = "extracted"
            self.db.commit()

            logger.info(
                "ExtractionService: completed document=%s requirements=%d",
                document_id,
                len(orm_rows),
            )

        except Exception as exc:
            self.db.rollback()
            logger.error(
                "ExtractionService: pipeline failed for document=%s: %s",
                document_id,
                str(exc)[:2000],
            )
            try:
                document.upload_status = "extraction_failed"
                self.db.commit()
            except Exception:
                self.db.rollback()
