import dataclasses
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from app.core.config import settings

if TYPE_CHECKING:
    from app.services.chunking.chunk_producer import ChunkRecord

logger = logging.getLogger(__name__)


class DebugWriter:
    def write(
        self,
        chunks: "list[ChunkRecord]",
        project_id: str,
        document_id: str,
    ) -> None:
        try:
            output_dir = Path(settings.chunking_debug_output_root)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{project_id}_{document_id}.json"
            data = [dataclasses.asdict(chunk) for chunk in chunks]
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.warning("DebugWriter: failed to write debug file: %s", exc)
