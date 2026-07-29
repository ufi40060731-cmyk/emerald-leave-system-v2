from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from rag.chunker import chunk_text
from rag.embeddings import hash_embedding
from rag.loaders import discover_documents, load_document


def build_index(
    documents_dir: Path,
    output_path: Path,
    *,
    max_chars: int = 900,
    overlap_chars: int = 150,
    dimensions: int = 256,
) -> dict:
    chunks: list[dict] = []
    document_count = 0
    skipped: list[dict] = []

    for path in discover_documents(documents_dir):
        try:
            document = load_document(path, documents_dir)
        except Exception as exc:
            skipped.append({"source": path.name, "error": str(exc)})
            continue
        document_count += 1
        for item in chunk_text(document.text, max_chars=max_chars, overlap_chars=overlap_chars):
            chunk_id = f"{document.source}#{item.index + 1}"
            chunks.append(
                {
                    "id": chunk_id,
                    "source": document.source,
                    "title": document.title,
                    "chunk_index": item.index,
                    "text": item.text,
                    "vector": hash_embedding(item.text, dimensions),
                }
            )

    payload = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "embedding": {"provider": "local-hash", "dimensions": dimensions},
        "documents": document_count,
        "chunks": chunks,
        "skipped": skipped,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Emerald local RAG index")
    parser.add_argument("--documents", type=Path, default=Path("rag/documents"))
    parser.add_argument("--output", type=Path, default=Path("rag/storage/index.json"))
    parser.add_argument("--max-chars", type=int, default=900)
    parser.add_argument("--overlap-chars", type=int, default=150)
    parser.add_argument("--dimensions", type=int, default=256)
    args = parser.parse_args()

    payload = build_index(
        args.documents,
        args.output,
        max_chars=args.max_chars,
        overlap_chars=args.overlap_chars,
        dimensions=args.dimensions,
    )
    print(
        f"RAG index created: {args.output} "
        f"({payload['documents']} documents, {len(payload['chunks'])} chunks)"
    )
    if payload["skipped"]:
        print(f"Skipped {len(payload['skipped'])} document(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
