"""
Core Engine — public functions called by the CLI/TUI.
"""
from core.retriever import retrieve
from core.generator import generate_answer


def ask(query: str) -> dict:
    """
    Runs the full retrieve -> generate flow for a one-shot question.
    Returns a dict with 'text' (the answer) and 'sources' (file paths).
    """
    chunks = retrieve(query)
    answer_text = generate_answer(query, chunks)

    sources = []
    seen_paths = set()
    for c in chunks:
        if c["file_path"] not in seen_paths:
            sources.append(c["file_path"])
            seen_paths.add(c["file_path"])

    return {
        "text": answer_text,
        "sources": sources,
    }