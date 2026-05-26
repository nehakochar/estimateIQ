"""
SemanticSplitter — wraps LlamaIndex SemanticSplitterNodeParser (primary)
and SentenceSplitter (fallback) to split a text chunk into semantically
coherent sub-chunks.

Stateless: a new parser instance is created on every call so that settings
changes are always picked up without restarting the process.
"""

import logging

from llama_index.core import Document as LlamaDocument
from llama_index.core.embeddings import resolve_embed_model
from llama_index.core.node_parser import SemanticSplitterNodeParser, SentenceSplitter

from app.core.config import settings

logger = logging.getLogger(__name__)


class SemanticSplitter:
    """Split a text string into semantically coherent sub-chunks.

    Primary strategy:  SemanticSplitterNodeParser (embedding-based)
    Fallback strategy: SentenceSplitter (token-based)
    Last resort:       return the original text as a single-element list
    """

    def split(self, text: str, section: str, chunk_index: int) -> list[str]:
        """Split *text* into sub-chunks.

        Args:
            text:        The raw text to split.
            section:     The section heading this chunk belongs to (used for
                         logging context only).
            chunk_index: The 0-based index of the source Phase 5 chunk (used
                         for logging).

        Returns:
            A non-empty list of non-empty text strings.
        """
        # ── Primary: SemanticSplitterNodeParser ──────────────────────────────
        try:
            embed_model = resolve_embed_model("local:BAAI/bge-small-en-v1.5")
            parser = SemanticSplitterNodeParser(
                buffer_size=settings.semantic_splitter_buffer_size,
                breakpoint_percentile_threshold=settings.semantic_splitter_breakpoint_percentile,
                embed_model=embed_model,
            )
            doc = LlamaDocument(text=text)
            nodes = parser.get_nodes_from_documents([doc])
            sub_texts = [n.get_content() for n in nodes if n.get_content().strip()]

            if sub_texts:
                logger.info(
                    "SemanticSplitter: chunk=%d split via SemanticSplitterNodeParser"
                    " \u2192 %d sub-chunks",
                    chunk_index,
                    len(sub_texts),
                )
                return sub_texts

            # Parser returned 0 usable nodes — fall through to SentenceSplitter
            logger.warning(
                "SemanticSplitter: chunk=%d SemanticSplitterNodeParser returned 0 nodes,"
                " falling back to SentenceSplitter",
                chunk_index,
            )

        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "SemanticSplitter: chunk=%d SemanticSplitterNodeParser failed (%s),"
                " falling back to SentenceSplitter",
                chunk_index,
                exc,
            )

        # ── Fallback: SentenceSplitter ────────────────────────────────────────
        splitter = SentenceSplitter(
            chunk_size=settings.semantic_sentence_chunk_size,
            chunk_overlap=settings.semantic_sentence_chunk_overlap,
        )
        doc = LlamaDocument(text=text)
        nodes = splitter.get_nodes_from_documents([doc])
        sub_texts = [n.get_content() for n in nodes if n.get_content().strip()]

        if sub_texts:
            return sub_texts

        # ── Last resort ───────────────────────────────────────────────────────
        return [text]
