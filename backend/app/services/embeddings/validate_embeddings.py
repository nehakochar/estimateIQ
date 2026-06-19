"""
validate_embeddings.py — CLI utility to validate an embedded_chunks.json file.

Usage:
    python validate_embeddings.py <path_to_embedded_chunks.json>

Prints:
    - Total chunk count
    - Number of successfully embedded chunks
    - Number of failed chunks
    - Details for any failed chunks (chunk_index and error field)

Exit codes:
    0 — success
    1 — missing or invalid arguments
    2 — file not found or JSON parse error
"""

import json
import sys
from pathlib import Path


def _usage() -> None:
    print("Usage: python validate_embeddings.py <path_to_embedded_chunks.json>")


def _load_chunks(path: Path) -> list[dict]:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: file not found: '{path}'")
        sys.exit(2)
    except json.JSONDecodeError as exc:
        print(f"Error: failed to parse JSON in '{path}': {exc}")
        sys.exit(2)

    if not isinstance(data, list):
        print(f"Error: expected a JSON array at the top level, got {type(data).__name__}.")
        sys.exit(2)

    return data


def main() -> None:
    if len(sys.argv) < 2:
        _usage()
        sys.exit(1)

    path = Path(sys.argv[1])
    chunks = _load_chunks(path)

    total = len(chunks)
    embedded_count = sum(
        1 for c in chunks if c.get("embedding_status") == "embedded"
    )
    failed_chunks = [
        c for c in chunks if c.get("embedding_status") == "failed"
    ]
    failed_count = len(failed_chunks)

    print("Embedded Chunks Validation Report")
    print("==================================")
    print(f"Total chunks:    {total}")
    print(f"Embedded:        {embedded_count}")
    print(f"Failed:          {failed_count}")

    if failed_chunks:
        print("\nFailed chunks:")
        for i, chunk in enumerate(failed_chunks):
            chunk_index = chunk.get("chunk_index", i)
            error = chunk.get("error", "<no error field>")
            print(f"  chunk_index={chunk_index}  error={error!r}")

    sys.exit(0)


if __name__ == "__main__":
    main()
