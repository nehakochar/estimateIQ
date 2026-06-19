"""
inspect_metadata.py — CLI utility for inspecting metadata quality of a classified_chunks.json file.

Usage:
    python inspect_metadata.py <path_to_classified_chunks.json>

Exit codes:
    0 — success
    1 — bad arguments or file not found
    2 — file read or JSON parse error
"""

import json
import sys


def main() -> None:
    # Validate arguments
    if len(sys.argv) < 2:
        print("Usage: python inspect_metadata.py <path_to_classified_chunks.json>")
        sys.exit(1)

    file_path = sys.argv[1]

    # Check file exists
    import os
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        print("Usage: python inspect_metadata.py <path_to_classified_chunks.json>")
        sys.exit(1)

    # Read and parse JSON
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw = f.read()
    except OSError as exc:
        print(f"Error: Could not read file '{file_path}': {exc}")
        sys.exit(2)

    try:
        chunks = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Error: Failed to parse JSON in '{file_path}': {exc}")
        sys.exit(2)

    if not isinstance(chunks, list):
        print(f"Error: Expected a JSON array at the top level, got {type(chunks).__name__}")
        sys.exit(2)

    # Compute statistics
    total = len(chunks)

    missing_section = sum(
        1 for c in chunks if not c.get("section", "")
    )
    missing_category = sum(
        1 for c in chunks if not c.get("category", "")
    )
    low_confidence = sum(
        1 for c in chunks if c.get("confidence_score", 0.0) < 0.5
    )

    token_counts = [c.get("token_count", 0) for c in chunks if "token_count" in c]

    if token_counts:
        min_tokens = min(token_counts)
        max_tokens = max(token_counts)
        avg_tokens = sum(token_counts) / len(token_counts)
    else:
        min_tokens = max_tokens = avg_tokens = 0

    # Print report
    print("=" * 50)
    print("  Metadata Quality Report")
    print("=" * 50)
    print(f"  Total chunks              : {total}")
    print(f"  Missing section           : {missing_section}")
    print(f"  Missing category          : {missing_category}")
    print(f"  Low confidence (< 0.5)    : {low_confidence}")
    print("-" * 50)
    if token_counts:
        print(f"  Token count — min         : {min_tokens}")
        print(f"  Token count — max         : {max_tokens}")
        print(f"  Token count — average     : {avg_tokens:.2f}")
    else:
        print("  Token count               : no data")
    print("=" * 50)


if __name__ == "__main__":
    main()
