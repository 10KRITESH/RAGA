"""
Answer Generator — builds a prompt from retrieved chunks and calls
Ollama to generate a natural-language answer.
"""
import ollama
from config import GENERATION_MODEL_DEFAULT, OLLAMA_HOST

_client = ollama.Client(host=OLLAMA_HOST)


def _build_prompt(query: str, chunks: list[dict]) -> str:
    context = "\n\n".join(
        f"[Source {i+1}: {c['file_path'].split('/')[-1]}]\n{c['chunk_text']}"
        for i, c in enumerate(chunks)
    )
    return f"""You are a helpful assistant that answers questions strictly based on the provided context.

IMPORTANT RULES:
- Read ALL sources carefully before answering.
- If the answer is present anywhere in the context, state it directly and clearly.
- Do NOT say "not mentioned" or "not explicitly mentioned" if the information IS present in the context.
- Only say you cannot find the answer if you have read all sources and it is genuinely absent.

Context:
{context}

Question: {query}

Answer:"""


def generate_answer(query: str, chunks: list[dict]) -> str:
    if not chunks:
        return "I couldn't find anything relevant to that in your indexed files."

    prompt = _build_prompt(query, chunks)
    response = _client.generate(
        model=GENERATION_MODEL_DEFAULT,
        prompt=prompt,
        options={
            "num_gpu": 99,    # push all layers to GPU
            "num_ctx": 4096,  # increased from 2048 so all 5 chunks fit comfortably
        },
    )
    return response["response"]
