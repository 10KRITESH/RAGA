"""
Core Engine — public functions called by the CLI/TUI (see API
Specification Section 1).

Query routing:
  filesystem → handle_filesystem_query()  (ls-style listing)
  location   → handle_location_query()    (find files by topic, no LLM)
  content    → retrieve() + generate_answer() (full RAG pipeline)
"""
from core.query_classifier import classify_query
from core.retriever import retrieve
from core.generator import generate_answer


def ask(query: str) -> dict:
    """
    Routes the query to the right handler and returns
    {'text': str, 'sources': list[str]}.
    """
    qtype = classify_query(query)

    # --- Filesystem queries: list/browse a directory ---
    if qtype == "filesystem":
        from core.filesystem_engine import handle_filesystem_query
        result = handle_filesystem_query(query)
        if result:
            return result
        # Couldn't resolve a path → fall through to content RAG

    # --- Location queries: find files by topic ---
    elif qtype == "location":
        from core.filesystem_engine import handle_location_query
        result = handle_location_query(query)
        if result:
            return result
        # Nothing found via path matching → fall through to content RAG

    # --- Content queries (and fallback) ---
    chunks = retrieve(query, top_k=7)
    answer_text = generate_answer(query, chunks)

    sources: list[str] = []
    seen: set[str] = set()
    for c in chunks:
        if c["file_path"] not in seen:
            sources.append(c["file_path"])
            seen.add(c["file_path"])

    return {"text": answer_text, "sources": sources}
