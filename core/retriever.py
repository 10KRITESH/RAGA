"""
Retriever — hybrid search combining vector similarity, BM25 full-text search,
and path/metadata matching.
Uses Weighted Reciprocal Rank Fusion (RRF) to merge signals.
"""
import re
from storage import vector_store
from ingestion.embedder import embed

# Common course/subject acronym expansions and keywords
ACRONYMS = {
    "ethical hacking": ["EH", "Ethical Hacking", "CyberSecurity", "Cyber Security"],
    "cyber security": ["CS", "CyberSecurity", "Cyber Security", "Security"],
    "machine learning": ["ML", "Machine Learning"],
    "deep learning": ["DL", "Deep Learning"],
    "artificial intelligence": ["AI"],
    "distributed computing": ["DC"],
    "biometrics": ["BM"],
    "cloud computing": ["AWS", "Cloud"],
}

STOPWORDS = {
    "where", "is", "are", "my", "the", "at", "in", "for", "of", "and", "to",
    "a", "an", "on", "with", "about", "what", "how", "show", "find", "get",
    "give", "tell", "me", "material", "materials", "study", "notes", "files",
    "file", "folder", "folders", "docs", "document", "documents", "project", "projects"
}


def _extract_path_patterns(query: str) -> list[str]:
    q_lower = query.lower()
    patterns = []

    # 1. Subject / Course acronym and exact phrase matches (e.g. /EH/, /CS/)
    for phrase, aliases in ACRONYMS.items():
        if phrase in q_lower:
            for alias in aliases:
                patterns.append(f"file_path LIKE '%/{alias}/%'")
                patterns.append(f"file_path LIKE '%/{alias}_%'")
                patterns.append(f"file_path LIKE '%/{alias} %'")
                patterns.append(f"file_path LIKE '%/{alias}%'")

    # 2. Significant keyword boundaries (e.g. folder name or filename matching word)
    words = [w for w in re.findall(r"[a-zA-Z0-9_-]+", q_lower) if w not in STOPWORDS and len(w) > 2]
    for w in words:
        patterns.append(f"file_path LIKE '%/{w}/%'")
        patterns.append(f"file_path LIKE '%/{w.capitalize()}/%'")
        patterns.append(f"file_path LIKE '%/{w.upper()}/%'")
        patterns.append(f"file_path LIKE '%/{w}%'")
        patterns.append(f"file_path LIKE '%/{w.capitalize()}%'")

    return patterns


def _diversify_chunks(chunks: list[dict], max_per_file: int = 2, top_k: int = 7) -> list[dict]:
    """Ensures results span multiple relevant files rather than being dominated by a single document."""
    counts: dict[str, int] = {}
    selected = []
    remaining = []

    for c in chunks:
        fp = c["file_path"]
        if counts.get(fp, 0) < max_per_file:
            selected.append(c)
            counts[fp] = counts.get(fp, 0) + 1
            if len(selected) == top_k:
                break
        else:
            remaining.append(c)

    if len(selected) < top_k:
        selected.extend(remaining[: (top_k - len(selected))])

    return selected


def _weighted_rrf(
    ranked_lists: list[tuple[list[dict], float]], k: int = 30
) -> list[dict]:
    """Weighted Reciprocal Rank Fusion combining multiple ranked result lists."""
    scores: dict[str, float] = {}
    chunks_by_id: dict[str, dict] = {}

    for results, weight in ranked_lists:
        for rank, chunk in enumerate(results):
            cid = chunk["chunk_id"]
            scores[cid] = scores.get(cid, 0.0) + weight / (k + rank + 1)
            chunks_by_id[cid] = chunk

    ranked = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)
    return [chunks_by_id[cid] for cid in ranked]


def retrieve(query: str, top_k: int = 7) -> list[dict]:
    query_vector = embed(query)
    table = vector_store.get_table()

    # 1. Semantic vector search (primary signal)
    vector_results = (
        table.search(query_vector)
        .limit(top_k * 4)
        .to_list()
    )

    # 2. BM25 full-text search on chunk content
    try:
        fts_results = (
            table.search(query, query_type="fts")
            .limit(top_k * 4)
            .to_list()
        )
    except Exception:
        fts_results = []

    # 3. Path / Folder keyword matching (crucial for "where is X / find my X notes")
    path_patterns = _extract_path_patterns(query)
    path_results = []
    if path_patterns:
        try:
            where_clause = " OR ".join(path_patterns[:15])
            path_results = table.search().where(where_clause).limit(top_k * 5).to_list()
        except Exception:
            path_results = []

    # 4. Merge: vector weight = 1.2, path match = 2.5 (strong signal for location/topic), FTS = 0.8
    ranked_lists = [(vector_results, 1.2)]
    if path_results:
        ranked_lists.append((path_results, 2.5))
    if fts_results:
        ranked_lists.append((fts_results, 0.8))

    merged = _weighted_rrf(ranked_lists, k=25)
    return _diversify_chunks(merged, max_per_file=2, top_k=top_k)
