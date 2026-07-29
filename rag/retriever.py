from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from rag.embeddings import cosine_similarity, hash_embedding

def _lexical_units(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKC", text).lower()
    compact = re.sub(r"\s+", "", normalized)
    words = set(re.findall(r"[\w]+", normalized, flags=re.UNICODE))
    bigrams = {compact[index:index + 2] for index in range(max(0, len(compact) - 1))}
    return {unit for unit in words | bigrams if unit}


def _lexical_overlap(question: str, text: str) -> float:
    query_units = _lexical_units(question)
    if not query_units:
        return 0.0
    text_units = _lexical_units(text)
    return len(query_units & text_units) / len(query_units)


class RagRetriever:
    def __init__(self, index_path: str | Path):
        self.index_path = Path(index_path)
        payload = json.loads(self.index_path.read_text(encoding="utf-8"))
        self.dimensions = int(payload["embedding"]["dimensions"])
        self.created_at = payload.get("created_at")
        self.chunks = list(payload.get("chunks", []))

    def search(self, question: str, top_k: int = 3, minimum_score: float = 0.03) -> list[dict]:
        query = question.strip()
        if not query:
            return []
        query_vector = hash_embedding(query, self.dimensions)
        results: list[dict] = []
        for chunk in self.chunks:
            vector_score = cosine_similarity(query_vector, chunk["vector"])
            lexical_score = _lexical_overlap(query, chunk["text"])
            score = vector_score + (0.45 * lexical_score)
            if score >= minimum_score:
                results.append(
                    {
                        "id": chunk["id"],
                        "source": chunk["source"],
                        "title": chunk["title"],
                        "text": chunk["text"],
                        "score": round(score, 6),
                        "vector_score": round(vector_score, 6),
                        "lexical_score": round(lexical_score, 6),
                    }
                )
        results.sort(key=lambda item: item["score"], reverse=True)
        return results[: max(1, min(top_k, 10))]

    def answer(self, question: str, top_k: int = 3) -> dict:
        matches = self.search(question, top_k=top_k)
        if not matches:
            return {
                "answer": "知識庫中找不到足夠相關的內容，請改用更明確的問題或更新文件索引。",
                "matches": [],
                "index_created_at": self.created_at,
            }
        best = matches[0]
        answer = f"根據《{best['title']}》：\n{best['text']}"
        return {"answer": answer, "matches": matches, "index_created_at": self.created_at}
