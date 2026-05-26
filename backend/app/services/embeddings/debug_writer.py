"""Debug writer for the embeddings pipeline.

Serialises embedded chunk data to disk after each pipeline run so that
developers can inspect what was stored in Qdrant without querying the
vector database directly.
"""

import json
import logging
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class DebugWriter:
    def write_embedded(
        self,
        chunks: list[dict],
        project_id: str,
        document_id: str,
    ) -> None:
        """Write embedded chunks snapshot to disk.

        Path: {settings.embedding_debug_output_root}/{project_id}_{document_id}_embedded_chunks.json
        Failures are non-fatal — a warning is logged and execution continues.
        """
        try:
            output_dir = Path(settings.embedding_debug_output_root)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{project_id}_{document_id}_embedded_chunks.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(chunks, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.warning("DebugWriter: failed to write embedded debug file: %s", exc)
