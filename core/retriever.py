"""
Retriever — hybrid search combining vector similarity, BM25 full-text search,
and path/metadata matching.
Uses Weighted Reciprocal Rank Fusion (RRF) to merge signals.
"""
import re
from storage import vector_store
from ingestion.embedder import embed

# Common course/subject acronym expansions and keywords.
# Keys are what the user might say (lowercase); values are folder/filename fragments.
ACRONYMS = {
    # SEM VII
    "computer networks": ["CN", "Computer Networks", "Computer Network"],
    "cn": ["CN", "Computer Networks"],
    "ethical hacking": ["EH", "Ethical Hacking", "CyberSecurity", "Cyber Security"],
    "eh": ["EH", "Ethical Hacking"],
    "data science": ["DS", "Data Science"],
    "ds": ["DS", "Data Science"],
    "internet of things": ["IOT", "IoT"],
    "iot": ["IOT", "IoT"],
    "operating systems": ["OS", "Operating System"],
    "os": ["OS", "Operating System"],
    "software engineering": ["SE", "Software Engineering"],
    "se": ["SE", "Software Engineering"],
    # SEM VI
    "cyber security": ["CS", "CyberSecurity", "Cyber Security"],
    "cs": ["CS", "CyberSecurity"],
    "machine learning": ["ML", "Machine Learning"],
    "ml": ["ML", "Machine Learning"],
    "deep learning": ["DL", "Deep Learning"],
    "dl": ["DL", "Deep Learning"],
    "distributed computing": ["DC"],
    "dc": ["DC"],
    "biometrics": ["BM"],
    "bm": ["BM"],
    "artificial intelligence": ["AI"],
    "ai": ["AI"],
    # SEM V / General
    "database": ["DBMS", "Database"],
    "dbms": ["DBMS", "Database"],
    "cloud computing": ["AWS", "Cloud"],
    "aws": ["AWS"],
}

STOPWORDS = {
    "where", "is", "are", "my", "the", "at", "in", "for", "of", "and", "to",
    "a", "an", "on", "with", "about", "what", "how", "show", "find", "get",
    "give", "tell", "me", "material", "materials", "study", "notes", "files",
    "file", "folder", "folders", "docs", "document", "documents", "project", "projects",
    "was", "did", "do", "it", "its", "that", "this", "there", "their",
    "experiment", "lab", "sem", "semester", "assignment", "no",
    # Roman numerals (semester numbers)
    "i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x",
}


def _extract_path_patterns(query: str) -> list[str]:
    q_lower = query.lower()
    # Pre-tokenize query words for whole-word matching against short ACRONYM keys
    query_words = set(re.findall(r"[a-zA-Z0-9]+", q_lower))
    patterns = []

    # 1. Subject / Course acronym and exact phrase matches (e.g. /EH/, /CS/, /CN/)
    # Use whole-word check for short keys (≤3 chars) to avoid "se" matching "semester"
    for phrase, aliases in ACRONYMS.items():
        phrase_words = phrase.split()
        if len(phrase_words) == 1 and len(phrase) <= 3:
            # Short single-word key: require exact token match
            matched = phrase in query_words
        else:
            # Multi-word or longer key: substring match is fine
            matched = phrase in q_lower

        if matched:
            for alias in aliases:
                patterns.append(f"file_path LIKE '%/{alias}/%'")
                patterns.append(f"file_path LIKE '%/{alias}_%'")
                patterns.append(f"file_path LIKE '%/{alias} %'")
                patterns.append(f"file_path LIKE '%/{alias}%'")

    # 2. Significant keyword / folder-name matching from query words
    # Allow 2-char words if they look like alphabetic acronyms (e.g. "cn", "os")
    words = [
        w for w in query_words
        if w not in STOPWORDS and (len(w) > 2 or (len(w) == 2 and w.isalpha()))
    ]
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
