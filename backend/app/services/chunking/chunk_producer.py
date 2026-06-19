"""
chunk_producer.py — Converts a HierarchyNode tree into flat ChunkRecord objects.

Strategy:
  - If a section's combined text (heading + body) is <= 800 tokens, keep it as
    a single chunk ("hierarchical").
  - If it exceeds 800 tokens, split with SentenceSplitter at 800 tokens /
    64-token overlap ("sentence_fallback").

Why remove HierarchicalNodeParser?
  LlamaIndex's HierarchicalNodeParser was splitting already-small sections into
  even smaller fragments. For RFP documents each section should stay as one
  meaningful chunk so the classifier and embedder have enough context to work with.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import tiktoken
from llama_index.core import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter

from app.services.chunking.hierarchy_builder import HierarchyNode

logger = logging.getLogger(__name__)

# Module-level tiktoken encoder — initialised once to avoid repeated disk I/O.
_ENCODING = tiktoken.get_encoding("cl100k_base")

# Maximum tokens per chunk before we fall back to sentence splitting.
_MAX_TOKENS = 800
# Overlap between consecutive sentence-split chunks.
_OVERLAP_TOKENS = 64


def _count_tokens(text: str) -> int:
    """Return the number of cl100k_base tokens in *text*."""
    return len(_ENCODING.encode(text))


@dataclass
class ChunkRecord:
    """A single flat chunk produced from a HierarchyNode."""

    text: str
    section: str
    subsection: str
    level: int
    page_number: int
    chunk_type: str              # "hierarchical" or "sentence_fallback"
    parent_chunk_index: int | None  # chunk_index of the parent node's first chunk
    chunk_index: int             # 0-based position across the whole document
    token_count: int


class ChunkProducer:
    """
    Converts a HierarchyNode tree into a flat list of ChunkRecord objects.

    Each section is kept as one chunk when it fits within _MAX_TOKENS (800).
    Sections that exceed 800 tokens are split with SentenceSplitter.
    """

    def produce(
        self,
        root_nodes: list[HierarchyNode],
        project_id: str,
        document_id: str,
    ) -> list[ChunkRecord]:
        """
        Traverse the HierarchyNode tree depth-first and produce ChunkRecords.

        Args:
            root_nodes:  Root-level nodes returned by HierarchyBuilder.
            project_id:  UUID string of the owning project (for logging).
            document_id: UUID string of the source document (for logging).

        Returns:
            Ordered list of ChunkRecord objects (0-based chunk_index).
        """
        records: list[ChunkRecord] = []
        # Mutable counter shared across the recursive traversal.
        counter: list[int] = [0]

        for root in root_nodes:
            self._process_node(
                node=root,
                records=records,
                counter=counter,
                parent_chunk_index=None,
                section=root.heading,
                subsection="",
            )

        # --- Logging ---
        total = len(records)
        hierarchical = sum(1 for r in records if r.chunk_type == "hierarchical")
        sentence_fallback = sum(1 for r in records if r.chunk_type == "sentence_fallback")
        logger.info(
            "ChunkProducer [doc=%s]: total_chunks=%d, hierarchical=%d, sentence_fallback=%d",
            document_id,
            total,
            hierarchical,
            sentence_fallback,
        )

        return records

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _process_node(
        self,
        node: HierarchyNode,
        records: list[ChunkRecord],
        counter: list[int],
        parent_chunk_index: int | None,
        section: str,
        subsection: str,
    ) -> None:
        """
        Recursively process a single node and all its descendants.

        The first chunk produced for this node becomes the "parent chunk" for
        the node's children (its chunk_index is passed down as parent_chunk_index).
        """
        # Derive section / subsection for this node.
        if node.level == 1:
            node_section = node.heading
            node_subsection = ""
        elif node.level == 2:
            node_section = section          # inherited from level-1 ancestor
            node_subsection = node.heading
        else:
            # level 3 (or deeper) — inherit both from ancestors
            node_section = section
            node_subsection = subsection

        combined_text = f"{node.heading}\n\n{node.body}"
        token_count_combined = _count_tokens(combined_text)

        if token_count_combined <= _MAX_TOKENS:
            # Section fits in one chunk — keep it whole for maximum context.
            chunk_texts = [combined_text]
            chunk_type = "hierarchical"
        else:
            # Section is too large — split with SentenceSplitter.
            chunk_texts = self._split_sentence(combined_text)
            chunk_type = "sentence_fallback"

        # The chunk_index of the *first* chunk produced for this node is used
        # as the parent_chunk_index for all of this node's children.
        first_chunk_index_for_node: int | None = None

        for text in chunk_texts:
            idx = counter[0]
            counter[0] += 1

            if first_chunk_index_for_node is None:
                first_chunk_index_for_node = idx

            records.append(
                ChunkRecord(
                    text=text,
                    section=node_section,
                    subsection=node_subsection,
                    level=node.level,
                    page_number=node.page_number,
                    chunk_type=chunk_type,
                    parent_chunk_index=parent_chunk_index,
                    chunk_index=idx,
                    token_count=_count_tokens(text),
                )
            )

        # Recurse into children, passing this node's first chunk index as parent.
        for child in node.children:
            self._process_node(
                node=child,
                records=records,
                counter=counter,
                parent_chunk_index=first_chunk_index_for_node,
                section=node_section,
                subsection=node_subsection,
            )

    # ------------------------------------------------------------------
    # Splitting strategy
    # ------------------------------------------------------------------

    def _split_sentence(self, text: str) -> list[str]:
        """
        Split *text* using LlamaIndex SentenceSplitter.

        Used only when a section exceeds _MAX_TOKENS (800) tokens.
        Respects sentence boundaries to avoid cutting mid-sentence.
        """
        splitter = SentenceSplitter(
            chunk_size=_MAX_TOKENS,
            chunk_overlap=_OVERLAP_TOKENS,
        )
        doc = LlamaDocument(text=text)
        nodes = splitter.get_nodes_from_documents([doc])
        texts = [n.get_content() for n in nodes if n.get_content().strip()]
        return texts if texts else [text]
