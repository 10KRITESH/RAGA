# Reranker — re-scores retrieved candidates for better precision.
# Uses MiniLM-L-6-v2 (~66MB) instead of bge-reranker-base (~1.1GB)
# because RAGA is a CLI tool that spawns a new process per query —
# the lighter model loads in ~1s vs 30s+ for the heavier one.

import torch
from sentence_transformers import CrossEncoder

# Lazy singleton — loaded on first rerank() call, not at import time.
# This avoids paying the ~1-2s cold-load cost on every fresh `uv run` process
# for code paths that don't use the reranker.
_model: CrossEncoder | None = None

def _get_model() -> CrossEncoder:
    global _model
    if _model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device=device)
    return _model

def rerank(query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
    if not chunks:
        return []

    # Include file metadata in what the cross-encoder sees, matching the
    # metadata-prefix approach used at index time for symmetric scoring.
    pairs = [
        (query, f"[File: {c['file_path'].split('/')[-1]} | Type: {c['source_type']}]\n{c['chunk_text']}")
        for c in chunks
    ]
    scores = _get_model().predict(pairs)

    scored_chunks = list(zip(chunks, scores))
    scored_chunks.sort(key=lambda x: x[1], reverse=True)

    return [chunk for chunk, score in scored_chunks[:top_k]]