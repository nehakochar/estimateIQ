"""
HierarchyBuilder — assembles a HierarchyNode tree from a flat list of
DetectedHeading objects and the full document text.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.services.chunking.heading_detector import DetectedHeading

logger = logging.getLogger(__name__)


@dataclass
class HierarchyNode:
    """A single node in the document hierarchy tree."""

    heading: str
    body: str
    level: int
    page_number: int
    children: list["HierarchyNode"] = field(default_factory=list)
    parent: "HierarchyNode | None" = field(default=None, repr=False)


class HierarchyBuilder:
    """Builds a HierarchyNode tree from detected headings and full document text."""

    def build(
        self,
        headings: list[DetectedHeading],
        full_text: str,
    ) -> list[HierarchyNode]:
        """
        Assemble a hierarchy of HierarchyNode objects from a flat heading list.

        Algorithm:
        - Maintain a stack of open nodes, one per active level.
        - For each heading (in document order):
            1. Extract body text = text between this heading's char_offset and
               the next heading's char_offset (or end of full_text).
            2. Pop the stack back until the top is at a strictly lower level
               than the current heading (i.e. find the nearest parent).
            3. Create a HierarchyNode and attach it as a child of the stack top,
               or as a root node if the stack is empty.
            4. Push the new node onto the stack.
        - Return the list of root nodes (level-1 nodes).

        Args:
            headings:  Ordered list of DetectedHeading objects.
            full_text: The full concatenated document text.

        Returns:
            List of root-level HierarchyNode objects in reading order.
        """
        if not headings:
            return []

        root_nodes: list[HierarchyNode] = []
        # Stack holds nodes that are still "open" (may receive children).
        # Invariant: stack is ordered by ascending level with no duplicates.
        stack: list[HierarchyNode] = []

        for i, heading in enumerate(headings):
            # --- Extract body text ---
            body_start = heading.char_offset + len(heading.text)
            if i + 1 < len(headings):
                body_end = headings[i + 1].char_offset
            else:
                body_end = len(full_text)

            body = full_text[body_start:body_end].strip()

            # --- Find parent: pop stack until top is at a lower level ---
            while stack and stack[-1].level >= heading.level:
                stack.pop()

            # --- Create node ---
            parent_node = stack[-1] if stack else None
            node = HierarchyNode(
                heading=heading.text,
                body=body,
                level=heading.level,
                page_number=heading.page_number,
                parent=parent_node,
            )

            # --- Attach to parent or root ---
            if parent_node is not None:
                parent_node.children.append(node)
            else:
                root_nodes.append(node)

            stack.append(node)

        # --- Compute stats and log ---
        total_nodes = self._count_nodes(root_nodes)
        max_depth = self._max_depth(root_nodes)
        logger.info(
            "HierarchyBuilder: total_nodes=%d, max_depth=%d",
            total_nodes,
            max_depth,
        )

        return root_nodes

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _count_nodes(self, nodes: list[HierarchyNode]) -> int:
        """Recursively count all nodes in the tree."""
        count = 0
        for node in nodes:
            count += 1 + self._count_nodes(node.children)
        return count

    def _max_depth(self, nodes: list[HierarchyNode], current_depth: int = 1) -> int:
        """Recursively compute the maximum depth of the tree."""
        if not nodes:
            return 0
        depths = [current_depth]
        for node in nodes:
            if node.children:
                depths.append(self._max_depth(node.children, current_depth + 1))
        return max(depths)
