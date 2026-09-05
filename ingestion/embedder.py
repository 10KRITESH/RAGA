# Wraps the embedding provider behind clean interfaces with batching support

import ollama
from config import EMBEDDING_MODEL, OLLAMA_HOST

_client = ollama.Client(host=OLLAMA_HOST)


def embed(text: str) -> list[float]:
    """Embed a single text string."""
    response = _client.embed(model=EMBEDDING_MODEL, input=text)
    return response.embeddings[0]


def embed_batch(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """Embed a list of text strings in concurrent batches for speed."""
    if not texts:
        return []
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = _client.embed(model=EMBEDDING_MODEL, input=batch)
        all_embeddings.extend(response.embeddings)
    return all_embeddings
