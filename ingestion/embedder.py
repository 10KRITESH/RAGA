# Wraps the embedding behind onee functino

import ollama
from config import EMBEDDING_MODEL, OLLAMA_HOST

_client = ollama.Client(host=OLLAMA_HOST)

def embed(text: str) -> list[float]:
    response = _client.embed(model=EMBEDDING_MODEL, input=text)
    return response.embeddings[0]
