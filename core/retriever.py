"""
Retriever — runs vector search + BM25 FTS independently, then merges
results using Reciprocal Rank Fusion (RRF). This avoids LanceDB's
hybrid search score imbalance where strong vector scores drown out BM25.
"""
from storage import vector_store
from ingestion.embedder import embed


def _rrf(results_lists: list[list[dict]], k: int = 60) -> list[dict]:
    """Reciprocal Rank Fusion — merges multiple ranked lists into one."""
    scores: dict[str, float] = {}
    chunks_by_id: dict[str, dict] = {}

    for results in results_lists:
        for rank, chunk in enumerate(results):
            cid = chunk["chunk_id"]
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
            chunks_by_id[cid] = chunk

    ranked = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)
    return [chunks_by_id[cid] for cid in ranked]


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    query_vector = embed(query)
    table = vector_store.get_table()

    # Run vector search (semantic)
    vector_results = (
        table.search(query_vector)
        .limit(top_k * 4)
        .to_list()
    )

    # Run BM25 full-text search (keyword)
    try:
        fts_results = (
            table.search(query, query_type="fts")
            .limit(top_k * 4)
            .to_list()
        )
    except Exception:
        fts_results = []

    # Merge with RRF and return top_k
    merged = _rrf([vector_results, fts_results])
    return merged[:top_k]
