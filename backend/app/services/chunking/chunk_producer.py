"""
ChunkProducer — converts a HierarchyNode tree into flat ChunkRecord objects
using LlamaIndex HierarchicalNodeParser (primary) and SentenceSplitter (fallback).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import tiktoken
from llama_index.core import Document as LlamaDocument
from llama_index.core.node_parser import HierarchicalNodeParser, SentenceSplitter

from app.core.config import settings
from app.services.chunking.hierarchy_builder import HierarchyNode

logger = logging.getLogger(__name__)

# Module-level tiktoken encoder — initialised once to avoid repeated disk I/O.
_ENCODING = tiktoken.get_encoding("cl100k_base")


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

    Primary strategy  : LlamaIndex HierarchicalNodeParser
    Fallback strategy : SentenceSplitter (when combined_text exceeds
                        settings.chunking_parent_chunk_size * 1.5 tokens)
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
        threshold = settings.chunking_parent_chunk_size * 1.5

        if token_count_combined <= threshold:
            chunk_texts = self._split_hierarchical(combined_text)
            chunk_type = "hierarchical"
        else:
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
    # Splitting strategies
    # ------------------------------------------------------------------

    def _split_hierarchical(self, text: str) -> list[str]:
        """
        Split *text* using LlamaIndex HierarchicalNodeParser.

        HierarchicalNodeParser is configured with the parent/child chunk sizes
        from settings. We wrap the text in a LlamaDocument, parse it, and
        return the text of every resulting node.

        If the parser produces no nodes (edge case with very short text), we
        fall back to returning the original text as a single chunk.
        """
        parser = HierarchicalNodeParser.from_defaults(
            chunk_sizes=[
                settings.chunking_parent_chunk_size,
                settings.chunking_child_chunk_size,
            ],
            chunk_overlap=settings.chunking_chunk_overlap,
        )
        doc = LlamaDocument(text=text)
        nodes = parser.get_nodes_from_documents([doc])

        texts = [n.get_content() for n in nodes if n.get_content().strip()]
        return texts if texts else [text]

    def _split_sentence(self, text: str) -> list[str]:
        """
        Split *text* using LlamaIndex SentenceSplitter (fallback strategy).

        Uses child chunk size and overlap from settings.
        """
        splitter = SentenceSplitter(
            chunk_size=settings.chunking_child_chunk_size,
            chunk_overlap=settings.chunking_chunk_overlap,
        )
        doc = LlamaDocument(text=text)
        nodes = splitter.get_nodes_from_documents([doc])

        texts = [n.get_content() for n in nodes if n.get_content().strip()]
        return texts if texts else [text]
