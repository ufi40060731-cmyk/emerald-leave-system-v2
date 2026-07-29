from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections import Counter


TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)


def _tokens(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", text).lower()
    words = TOKEN_RE.findall(normalized)
    compact = re.sub(r"\s+", "", normalized)
    char_ngrams = [compact[i:i + 3] for i in range(max(0, len(compact) - 2))]
    return words + char_ngrams


def hash_embedding(text: str, dimensions: int = 256) -> list[float]:
    """Create a deterministic local vector without sending text to an external API."""
    if dimensions < 64:
        raise ValueError("dimensions must be at least 64")

    counts = Counter(_tokens(text))
    vector = [0.0] * dimensions
    for token, count in counts.items():
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=16).digest()
        bucket = int.from_bytes(digest[:8], "big") % dimensions
        sign = -1.0 if digest[8] & 1 else 1.0
        vector[bucket] += sign * (1.0 + math.log(count))

    norm = math.sqrt(sum(value * value for value in vector))
    if norm:
        vector = [round(value / norm, 8) for value in vector]
    return vector


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Vectors must use the same dimensions")
    return sum(a * b for a, b in zip(left, right))
