"""
EmbeddingService — loads the BAAI/bge-small-en-v1.5 SentenceTransformer model once
at instantiation and produces normalised 384-dimensional dense vector embeddings from
a list of text strings. The model instance is reused across all calls to avoid the
overhead of reloading it on every invocation.
"""

import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Wraps the BAAI/bge-small-en-v1.5 SentenceTransformer model.

    The model is loaded in ``__init__``. If loading fails the exception
    propagates to the caller (typically ``EmbeddingPipeline``) so it can
    mark the document as ``"embedding_failed"``.
    """

    def __init__(self) -> None:
        logger.info("EmbeddingService: loading model BAAI/bge-small-en-v1.5")
        self._model: SentenceTransformer = SentenceTransformer("BAAI/bge-small-en-v1.5")
        logger.info("EmbeddingService: model loaded successfully")

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return normalised 384-dimensional embeddings for each input text.

        Args:
            texts: A list of strings to embed.

        Returns:
            A ``list[list[float]]`` where each inner list has exactly 384
            elements. Returns an empty list when *texts* is empty.
        """
        if not texts:
            return []

        embeddings = self._model.encode(texts, normalize_embeddings=True)
        # encode() returns a numpy ndarray — convert to plain Python lists
        return embeddings.tolist()
