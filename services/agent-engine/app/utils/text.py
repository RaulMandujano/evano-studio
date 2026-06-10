"""Plain-text utilities (chunking for RAG)."""

from __future__ import annotations


def chunk_text(text: str, size: int = 1000, overlap: int = 150) -> list[str]:
    """Split text into overlapping character windows.

    Prefers to break at a paragraph/sentence/word boundary near the window end so
    chunks stay readable. Overlap preserves context across chunk boundaries.
    """
    text = (text or "").strip()
    if not text:
        return []
    if size <= 0:
        return [text]
    overlap = max(0, min(overlap, size - 1))

    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        if end < n:
            window = text[start:end]
            # Prefer a clean break point in the latter half of the window.
            candidates = [window.rfind("\n\n"), window.rfind("\n"), window.rfind(". "), window.rfind(" ")]
            cut = max(candidates)
            if cut > size // 2:
                end = start + cut + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = max(0, end - overlap)
    return chunks
