"""
inspect_vectors.py — CLI utility to inspect Qdrant vectors for a given project.

Usage:
    python inspect_vectors.py --project-id <uuid>

Prints:
    - Total vector count for the project
    - First 5 payloads with category, chunk_type, page, and text (truncated to 100 chars)

Exit codes:
    0 — success
    1 — missing or invalid arguments (handled automatically by argparse)
    2 — Qdrant connection or query error
"""

import argparse
import sys


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect Qdrant vectors stored for a given project."
    )
    parser.add_argument(
        "--project-id",
        required=True,
        metavar="UUID",
        help="The project UUID whose vectors should be inspected.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    project_id: str = args.project_id

    try:
        from app.services.vector.qdrant_service import QdrantService

        qdrant_service = QdrantService()
        count = qdrant_service.get_vector_count(project_id)
        payloads = qdrant_service.inspect_vectors({"project_id": project_id})
    except Exception as exc:
        print(f"Error: failed to connect to or query Qdrant: {exc}")
        sys.exit(2)

    print(f"Vector count for project {project_id}: {count}")

    if payloads:
        print("\nFirst 5 payloads:")
        for i, payload in enumerate(payloads[:5], start=1):
            category = payload.get("category", "")
            chunk_type = payload.get("chunk_type", "")
            page = payload.get("page", "")
            text = payload.get("text", "")
            truncated_text = text[:100]
            print(f"[{i}] category={category}  chunk_type={chunk_type}  page={page}")
            print(f"    text: {truncated_text}...")


if __name__ == "__main__":
    main()
