"""
Retriever — embeds a query and finds the most similar stored chunks
in LanceDB (see System Design Section 3.4).
"""
from storage import vector_store
from ingestion.embedder import embed


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    """
    Returns the top_k most similar chunks to the query, each as a dict
    with chunk_text, file_path, and a relevance score.
    """
    query_vector = embed(query)

    table = vector_store.get_table()
    results = (
        table.search(query_vector)
        .limit(top_k)
        .to_list()
    )

    return results