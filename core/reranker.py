"""
Reranker — re-scores retrieved candidates for high precision.
Uses local MiniLM-L-6-v2 (~66MB) with background warm-up for instant inference.
"""
import os
import torch

# Silence HuggingFace network pings and progress bars
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from sentence_transformers import CrossEncoder

_model: CrossEncoder | None = None


def warmup_reranker() -> None:
    """Pre-loads the CrossEncoder weights in the background so queries have 0ms latency."""
    _get_model()


def _get_model() -> CrossEncoder:
    global _model
    if _model is None:
        torch.set_grad_enabled(False)
        device = "cpu"
        try:
            # Try fast local-only load first
            _model = CrossEncoder(
                "cross-encoder/ms-marco-MiniLM-L-6-v2",
                device=device,
                local_files_only=True,
            )
        except Exception:
            _model = CrossEncoder(
                "cross-encoder/ms-marco-MiniLM-L-6-v2",
                device=device,
            )
    return _model


def rerank(query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
    if not chunks:
        return []

    pairs = [
        (query, f"[File: {c['file_path'].split('/')[-1]} | Type: {c['source_type']}]\n{c['chunk_text']}")
        for c in chunks
    ]
    scores = _get_model().predict(pairs, show_progress_bar=False)
    import math

    scored_chunks = []
    for chunk, raw_score in zip(chunks, scores):
        s_val = float(raw_score)
        # Sigmoid normalization for realistic 0-100% confidence display
        norm_score = 1.0 / (1.0 + math.exp(-max(min(s_val, 20), -20)))
        chunk_copy = dict(chunk)
        chunk_copy["score"] = norm_score
        chunk_copy["raw_score"] = s_val
        scored_chunks.append((chunk_copy, s_val))

    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    return [chunk for chunk, _ in scored_chunks[:top_k]]

