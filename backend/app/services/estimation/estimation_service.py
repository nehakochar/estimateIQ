import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.requirement_estimate import RequirementEstimate
from app.models.extracted_requirement import ExtractedRequirement

logger = logging.getLogger(__name__)

class EstimationService:
    """Service to generate sub‑feature estimates for a requirement.

    It loads the extracted requirement, constructs a prompt, calls the LLM via the
    generic `call_llm` helper (re‑using the same pattern as ExtractionService),
    parses the JSON response into sub‑features and persists them.
    """

    def __init__(self, project_id: str, db: Session | None = None):
        self.project_id = uuid.UUID(project_id)
        self.db = db or self._get_session()
        self.llm_provider = settings.extraction_provider  # reuse same provider config

    def _get_session(self) -> Session:
        # Import lazily to avoid circular imports
        from app.core.database import SessionLocal
        return SessionLocal()

    def _load_requirement(self, requirement_id: str) -> ExtractedRequirement:
        req_uuid = uuid.UUID(requirement_id)
        req = self.db.get(ExtractedRequirement, req_uuid)
        if not req:
            raise ValueError(f"Requirement {requirement_id} not found")
        return req

    def _build_prompt(self, req: ExtractedRequirement) -> str:
        return (
            "You are a senior solution architect. For the following software requirement, generate all development sub‑features needed for implementation, with effort estimates for Frontend, Backend, and Mobile (set to 0 if mobile is not relevant).\n\n"
            f"Requirement:\n  ID: {req.id}\n  Name: {req.name}\n  Type: {req.req_type}\n  Description: {req.description}\n\n"
            "Return ONLY a valid JSON array. Each item must have exactly these fields:\n"
            "{\n"
            "  \"sub_feature_name\": \"...\",\n"
            "  \"description\": \"...\",\n"
            "  \"frontend_hours\": <number>,\n"
            "  \"backend_hours\": <number>,\n"
            "  \"mobile_hours\": <number>,\n"
            "  \"complexity\": \"Low | Medium | High\",\n"
            "  \"assumptions\": \"...\"\n"
            "}\n\n"
            "Account for UI implementation, API development, DB changes, auth/authorization, validation, error handling, testing, and third‑party integrations where relevant. Return [] if no development sub‑tasks are needed."
        )

    def _call_llm(self, prompt: str) -> str:
        # Re‑use the same provider logic from ExtractionService
        if self.llm_provider.lower() == "gemini":
            from app.services.extraction.extraction_service import _call_gemini
            return _call_gemini(prompt)
        elif self.llm_provider.lower() == "groq":
            from app.services.extraction.extraction_service import _call_groq
            return _call_groq(prompt)
        else:
            raise ValueError(f"Unsupported provider {self.llm_provider}")

    def _parse_response(self, raw: str) -> list[dict]:
        import json, re
        raw = raw.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return data
            # If wrapped in an object, try to extract a list value
            for v in data.values():
                if isinstance(v, list):
                    return v
            logger.warning("EstimationService: LLM returned a dict with no list value; raw[:200]=%s", raw[:200])
            return []
        except json.JSONDecodeError as exc:
            # Log the raw response so it can be audited, then raise so the task
            # knows this requirement failed (instead of silently writing 0 sub-features).
            logger.error(
                "EstimationService: JSON parse failed for requirement. Error: %s. Raw[:500]: %s",
                exc,
                raw[:500],
            )
            raise

    def run(self, requirement_id: str) -> int:
        """Generate and persist sub-feature estimates for a single requirement.

        Returns the number of sub-features persisted.
        Raises on LLM or parse failure so the caller (Celery task) can decide
        whether to continue or abort.
        """
        req = self._load_requirement(requirement_id)
        prompt = self._build_prompt(req)
        logger.debug("EstimationService: calling LLM for requirement %s", requirement_id)
        raw = self._call_llm(prompt)  # raises on failure — propagate to task
        logger.debug("EstimationService: raw LLM response (first 300 chars): %s", raw[:300])
        sub_features = self._parse_response(raw)  # raises on JSON error

        # Clean existing estimates for this requirement first
        self.db.query(RequirementEstimate).filter(
            RequirementEstimate.requirement_id == req.id
        ).delete(synchronize_session=False)

        # Insert new estimates
        for idx, sf in enumerate(sub_features):
            mobile_hours = float(sf.get("mobile_hours", 0) or 0)
            if req.req_type not in ("Functional", "Integration"):
                mobile_hours = 0.0

            estimate = RequirementEstimate(
                requirement_id=req.id,
                project_id=self.project_id,
                sub_feature_name=sf.get("sub_feature_name", "Unnamed"),
                description=sf.get("description", ""),
                frontend_hours=float(sf.get("frontend_hours", 0) or 0),
                backend_hours=float(sf.get("backend_hours", 0) or 0),
                mobile_hours=mobile_hours,
                complexity=sf.get("complexity", "Low"),
                assumptions=sf.get("assumptions") or "",  # default empty string, never None
                sort_order=idx,
            )
            self.db.add(estimate)

        self.db.commit()
        logger.info(
            "EstimationService: persisted %d sub-features for requirement %s",
            len(sub_features),
            requirement_id,
        )
        return len(sub_features)
