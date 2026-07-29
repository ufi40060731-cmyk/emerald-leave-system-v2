from __future__ import annotations

import argparse
from pathlib import Path

from rag.retriever import RagRetriever


def main() -> int:
    parser = argparse.ArgumentParser(description="Search the Emerald RAG index")
    parser.add_argument("question")
    parser.add_argument("--index", type=Path, default=Path("rag/storage/index.json"))
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    result = RagRetriever(args.index).answer(args.question, top_k=args.top_k)
    print(result["answer"])
    for match in result["matches"]:
        print(f"\n[{match['score']:.3f}] {match['source']} ({match['id']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
