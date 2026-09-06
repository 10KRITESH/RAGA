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
    "cloud computing": ["CC", "Cloud Computing"],
    "cc": ["CC", "Cloud Computing"],
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
    "rpa": ["RPA"],
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
    # Projects / General
    "capstone": ["CAPSTONE", "Capstone"],
    "database": ["DBMS", "Database"],
    "dbms": ["DBMS", "Database"],
    "cloud": ["AWS", "Cloud"],
    "aws": ["AWS"],
}

STOPWORDS = {
    "where", "is", "are", "my", "the", "at", "in", "for", "of", "and", "to",
    "a", "an", "on", "with", "about", "what", "how", "show", "find", "get",
    "give", "tell", "me", "material", "materials", "study", "notes", "files",
    "file", "folder", "folders", "docs", "document", "documents", "project", "projects",
    "resource", "resources", "resouces", "all", "have", "i",
    "was", "did", "do", "it", "its", "that", "this", "there", "their",
    "experiment", "lab", "sem", "semester", "assignment", "no",
    # Query & Document metadata noise words
    "who", "author", "authors", "wrote", "written", "by", "paper", "papers",
    "presentation", "summary", "overview", "explain", "describe", "detail", "details",
    "pdf", "docx", "doc", "txt", "code",
    # Roman numerals (semester numbers)
    "i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x",
}


def _extract_path_patterns(query: str) -> list[str]:
    q_lower = query.lower()
    query_words = set(re.findall(r"[a-zA-Z0-9]+", q_lower))
    patterns = []

    # 1. Subject / Course acronym matches (e.g. /EH/, /CS/, /CN/, /CC/)
    for phrase, aliases in ACRONYMS.items():
        phrase_words = phrase.split()
        if len(phrase_words) == 1 and len(phrase) <= 3:
            matched = phrase in query_words
        else:
            matched = phrase in q_lower

        if matched:
            for alias in aliases:
                patterns.append(f"file_path ILIKE '%/{alias}/%'")
                patterns.append(f"file_path ILIKE '%/{alias}_%'")
                patterns.append(f"file_path ILIKE '%/{alias} %'")
                patterns.append(f"file_path ILIKE '%/{alias}-%'")
                patterns.append(f"file_path ILIKE '%/{alias}%'")

    # 2. Significant keyword / filename matching using case-insensitive ILIKE
    words = [
        w for w in query_words
        if w not in STOPWORDS and (len(w) > 2 or (len(w) == 2 and w.isalpha()))
    ]
    for w in words:
        if len(w) <= 3:
            patterns.append(f"file_path ILIKE '%/{w}/%'")
            patterns.append(f"file_path ILIKE '%/{w}_%'")
            patterns.append(f"file_path ILIKE '%/{w} %'")
            patterns.append(f"file_path ILIKE '%/{w}-%'")
        else:
            patterns.append(f"file_path ILIKE '%/{w}/%'")
            patterns.append(f"file_path ILIKE '%{w}%'")

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


CONTAINER_SCOPES: dict[str, str] = {
    "projects": "projects",
    "project": "projects",
    "sem vii": "SEM VII",
    "sem 7": "SEM VII",
    "semester 7": "SEM VII",
    "sem vi": "SEM VI",
    "sem 6": "SEM VI",
    "semester 6": "SEM VI",
    "sem v": "SEM V",
    "sem 5": "SEM V",
    "semester 5": "SEM V",
    "capstone": "CAPSTONE",
    "nptel": "NPTEL",
    "aws material": "AWS Material",
    "saa notes": "SAA NOTES",
}


def _detect_scope(query: str) -> str | None:
    q_lower = query.lower()
    for phrase, scope in sorted(CONTAINER_SCOPES.items(), key=lambda x: len(x[0]), reverse=True):
        if phrase in q_lower:
            return scope
    return None


def retrieve(query: str, top_k: int = 7) -> list[dict]:
    query_vector = embed(query)
    table = vector_store.get_table()
    ranked_lists = []

    scope = _detect_scope(query)

    # 1. Scoped search (if user specifies a domain like 'projects', 'sem vii', etc.)
    if scope:
        try:
            scoped_where = f"file_path ILIKE '%/{scope}/%'"
            scoped_vec = table.search(query_vector).where(scoped_where).limit(top_k * 4).to_list()
            if scoped_vec:
                ranked_lists.append((scoped_vec, 3.5))

            # Strip scope word from query for scoped FTS
            clean_q = re.sub(rf"\b{re.escape(scope)}\b", "", query, flags=re.IGNORECASE).strip()
            if clean_q:
                scoped_fts = table.search(clean_q, query_type="fts").where(scoped_where).limit(top_k * 4).to_list()
                if scoped_fts:
                    ranked_lists.append((scoped_fts, 2.5))
        except Exception:
            pass

    # 2. Semantic vector search (primary global signal)
    vector_results = (
        table.search(query_vector)
        .limit(top_k * 4)
        .to_list()
    )
    ranked_lists.append((vector_results, 1.2))

    # 3. BM25 full-text search on chunk content
    try:
        fts_results = (
            table.search(query, query_type="fts")
            .limit(top_k * 4)
            .to_list()
        )
        if fts_results:
            ranked_lists.append((fts_results, 0.8))
    except Exception:
        pass

    # 4. Path / Folder keyword matching (case-insensitive ILIKE)
    path_patterns = _extract_path_patterns(query)
    if path_patterns:
        try:
            where_clause = " OR ".join(path_patterns[:15])
            path_results = table.search().where(where_clause).limit(top_k * 5).to_list()
            if path_results:
                ranked_lists.append((path_results, 2.5))
        except Exception:
            pass

    merged = _weighted_rrf(ranked_lists, k=25)

    # For top matched files, guarantee Chunk 0 (header/author/title) is available
    top_file_paths = {c["file_path"] for c in merged[:5]}
    chunk_0s = []
    if top_file_paths:
        try:
            paths_condition = " OR ".join([f"file_path = '{fp}'" for fp in top_file_paths])
            header_results = table.search().where(f"chunk_index = 0 AND ({paths_condition})").limit(len(top_file_paths)).to_list()
            chunk_0s = header_results
        except Exception:
            chunk_0s = []

    combined = chunk_0s + merged
    # Deduplicate preserving order
    seen_ids = set()
    deduped = []
    for c in combined:
        if c["chunk_id"] not in seen_ids:
            seen_ids.add(c["chunk_id"])
            deduped.append(c)

    # 5. CrossEncoder Reranking: re-scores candidate pool for high precision
    try:
        from core.reranker import rerank
        candidates_to_rerank = deduped[:25]
        reranked = rerank(query, candidates_to_rerank, top_k=top_k * 2)
        if reranked:
            deduped = reranked
    except Exception:
        pass

    return _diversify_chunks(deduped, max_per_file=2, top_k=top_k)
