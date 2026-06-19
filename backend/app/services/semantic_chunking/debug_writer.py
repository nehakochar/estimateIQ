import json
import logging
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class DebugWriter:
    def write_semantic(
        self,
        chunks: list[dict],
        project_id: str,
        document_id: str,
    ) -> None:
        """Write pre-classification semantic chunks snapshot to disk.

        Path: {settings.semantic_debug_output_root}/{project_id}_{document_id}_semantic.json
        Failures are non-fatal — a warning is logged and execution continues.
        """
        try:
            output_dir = Path(settings.semantic_debug_output_root)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{project_id}_{document_id}_semantic.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(chunks, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.warning("DebugWriter: failed to write semantic debug file: %s", exc)

    def write_classified(
        self,
        chunks: list[dict],
        project_id: str,
        document_id: str,
    ) -> None:
        """Write post-classification chunks snapshot to disk.

        Path: {settings.semantic_debug_output_root}/{project_id}_{document_id}_classified.json
        Failures are non-fatal — a warning is logged and execution continues.
        """
        try:
            output_dir = Path(settings.semantic_debug_output_root)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{project_id}_{document_id}_classified.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(chunks, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.warning("DebugWriter: failed to write classified debug file: %s", exc)
