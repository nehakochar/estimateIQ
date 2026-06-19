"""
inspect_chunks.py — CLI utility to inspect a classified_chunks.json file.

Usage:
    python inspect_chunks.py <path_to_classified_chunks.json>

Prints:
    - A summary table of chunk count per category
    - The first 3 chunks per category with text (truncated to 120 chars),
      confidence_score, and token_count
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

TEXT_TRUNCATE_LEN = 120
PREVIEW_CHUNKS_PER_CATEGORY = 3


def _usage() -> None:
    print("Usage: python inspect_chunks.py <path_to_classified_chunks.json>")


def _load_chunks(path: Path) -> list[dict]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Error reading file '{path}': {exc}")
        sys.exit(2)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Error parsing JSON in '{path}': {exc}")
        sys.exit(2)

    if not isinstance(data, list):
        print(f"Error: expected a JSON array at the top level, got {type(data).__name__}.")
        sys.exit(2)

    return data


def _print_summary(category_chunks: dict[str, list[dict]]) -> None:
    print("\n=== Category Summary ===")
    print(f"{'Category':<40} {'Count':>6}")
    print("-" * 48)
    for category in sorted(category_chunks.keys()):
        count = len(category_chunks[category])
        print(f"{category:<40} {count:>6}")
    total = sum(len(v) for v in category_chunks.values())
    print("-" * 48)
    print(f"{'TOTAL':<40} {total:>6}")


def _print_previews(category_chunks: dict[str, list[dict]]) -> None:
    print("\n=== Chunk Previews (first 3 per category) ===")
    for category in sorted(category_chunks.keys()):
        chunks = category_chunks[category]
        print(f"\n--- {category} ({len(chunks)} chunk(s)) ---")
        for i, chunk in enumerate(chunks[:PREVIEW_CHUNKS_PER_CATEGORY]):
            text = chunk.get("text", "")
            if len(text) > TEXT_TRUNCATE_LEN:
                text = text[:TEXT_TRUNCATE_LEN] + "…"
            confidence = chunk.get("confidence_score", "N/A")
            token_count = chunk.get("token_count", "N/A")
            print(f"  [{i + 1}] text        : {text!r}")
            print(f"       confidence  : {confidence}")
            print(f"       token_count : {token_count}")


def main() -> None:
    if len(sys.argv) < 2:
        _usage()
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Error: path does not exist: '{path}'")
        _usage()
        sys.exit(1)

    chunks = _load_chunks(path)

    # Group chunks by category
    category_chunks: dict[str, list[dict]] = defaultdict(list)
    for chunk in chunks:
        category = chunk.get("category", "")
        category_chunks[category].append(chunk)

    _print_summary(category_chunks)
    _print_previews(category_chunks)


if __name__ == "__main__":
    main()
