"""
Answer Generator — builds a prompt from retrieved chunks and calls
Ollama to generate a natural-language answer.
"""
import ollama
from config import GENERATION_MODEL_DEFAULT, OLLAMA_HOST

_client = ollama.Client(host=OLLAMA_HOST)


def _build_prompt(query: str, chunks: list[dict]) -> str:
    context = "\n\n".join(
        f"[Source: {c['file_path']}]\n{c['chunk_text']}"
        for c in chunks
    )
    return f"""You are a helpful assistant that answers questions about the user's own files.
Use ONLY the context below to answer. If the context doesn't contain the answer, say so honestly.

Context:
{context}

Question: {query}

Answer:"""


def generate_answer(query: str, chunks: list[dict]) -> str:
    if not chunks:
        return "I couldn't find anything relevant to that in your indexed files."

    prompt = _build_prompt(query, chunks)
    response = _client.generate(model=GENERATION_MODEL_DEFAULT, prompt=prompt)
    return response["response"]