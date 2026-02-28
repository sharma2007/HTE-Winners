from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    text: str


def chunk_text(text: str, target_chars: int = 900, overlap_chars: int = 120) -> list[TextChunk]:
    text = (text or "").strip()
    if not text:
        return []

    chunks: list[TextChunk] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + target_chars)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(TextChunk(text=chunk))
        if end >= n:
            break
        start = max(0, end - overlap_chars)
    return chunks

