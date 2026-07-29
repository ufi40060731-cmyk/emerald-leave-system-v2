from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    index: int
    text: str


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\t\u00a0]+", " ", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, max_chars: int = 900, overlap_chars: int = 150) -> list[TextChunk]:
    if max_chars < 200:
        raise ValueError("max_chars must be at least 200")
    if overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("overlap_chars must be between 0 and max_chars - 1")

    normalized = normalize_text(text)
    if not normalized:
        return []

    chunks: list[TextChunk] = []
    start = 0
    length = len(normalized)
    while start < length:
        end = min(start + max_chars, length)
        if end < length:
            search_start = min(start + max_chars // 2, end)
            candidates = [
                normalized.rfind("\n\n", search_start, end),
                normalized.rfind("。", search_start, end),
                normalized.rfind(". ", search_start, end),
                normalized.rfind("\n", search_start, end),
            ]
            boundary = max(candidates)
            if boundary > start:
                end = boundary + (2 if normalized[boundary:boundary + 2] == "\n\n" else 1)

        piece = normalized[start:end].strip()
        if piece:
            chunks.append(TextChunk(index=len(chunks), text=piece))
        if end >= length:
            break
        start = max(end - overlap_chars, start + 1)

    return chunks
