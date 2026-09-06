"""
Answer Generator — builds a prompt from retrieved chunks, routes between general
and code-specialized models, and calls Ollama to generate a natural-language answer.
"""
from pathlib import Path
import ollama
from config import GENERATION_MODEL_DEFAULT, GENERATION_MODEL_CODE, OLLAMA_HOST

_client = ollama.Client(host=OLLAMA_HOST)

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".rs", ".go", ".c", ".cpp",
    ".h", ".hpp", ".java", ".kt", ".lua", ".zig", ".rb", ".php",
    ".sh", ".bash", ".zsh", ".sql", ".html", ".css"
}

CODE_KEYWORDS = {
    "function", "class", "method", "def ", "func ", "const ", "let ",
    "var ", "return", "import ", "export", "syntax", "compile",
    "debug", "refactor", "bug", "traceback", "exception", "code",
    "script", "regex", "algorithm", "parameter", "arguments"
}


def _format_size(size_bytes: int) -> str:
    if size_bytes >= 1024 * 1024 * 1024:
        return f"{size_bytes / (1024**3):.2f} GB"
    elif size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024**2):.2f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes} B"


def _select_model(query: str, chunks: list[dict]) -> str:
    """Routes query to code-specialized model or general model based on context and query."""
    if chunks:
        code_chunks = sum(
            1 for c in chunks
            if any(c.get("file_path", "").endswith(ext) for ext in CODE_EXTENSIONS)
            or c.get("source_type") == "code"
        )
        if (code_chunks / len(chunks)) >= 0.4:
            return GENERATION_MODEL_CODE

    q_lower = query.lower()
    if any(kw in q_lower for kw in CODE_KEYWORDS):
        return GENERATION_MODEL_CODE

    return GENERATION_MODEL_DEFAULT


def _build_prompt(query: str, chunks: list[dict], history: list[dict] | None = None) -> str:
    context_blocks = []
    for i, c in enumerate(chunks):
        p = Path(c["file_path"])
        file_info = p.name
        if p.exists():
            try:
                stat = p.stat()
                size_str = _format_size(stat.st_size)
                file_info += f" | Size: {size_str} | Path: {p.resolve()}"
            except Exception:
                pass
        context_blocks.append(f"[Source {i+1}: {file_info}]\n{c['chunk_text']}")

    context = "\n\n".join(context_blocks)

    history_str = ""
    if history:
        turns = []
        for msg in history[-4:]:
            role = "User" if msg.get("role") == "user" else "Assistant"
            turns.append(f"{role}: {msg.get('content', '')}")
        if turns:
            history_str = "\nRecent Conversation History:\n" + "\n".join(turns) + "\n"

    return f"""You are RAGA, an intelligent local assistant for the user's computer.
The provided context contains excerpts and metadata from files stored locally on the user's system.

GUIDELINES:
- Answer the user's question directly and concisely based on the context and source metadata.
- When the user asks where files, notes, or study materials are located, clearly point out the file paths and folder locations from the source headers and summarize what is in each.
- When synthesizing answers or answering questions about content, cite the relevant files and paths.
- If the conversation history is relevant (e.g. follow-up questions, pronouns referencing previous turns), use it for conversational context.
- If the context contains relevant information, answer thoroughly without guessing.
- Only say you cannot find the information if the provided context is genuinely unrelated.

Context:
{context}
{history_str}
Question: {query}

Answer:"""


def generate_answer(query: str, chunks: list[dict], history: list[dict] | None = None) -> str:
    if not chunks:
        return "I couldn't find anything relevant to that in your indexed files."

    model = _select_model(query, chunks)
    prompt = _build_prompt(query, chunks, history=history)

    response = _client.generate(
        model=model,
        prompt=prompt,
        options={
            "num_gpu": 99,    # push all layers to GPU
            "num_ctx": 4096,  # comfortable context window for all chunks
        },
    )
    return response["response"]


def generate_answer_streaming(query: str, chunks: list[dict], history: list[dict] | None = None):
    """
    Streaming version — yields response tokens as they arrive from Ollama.
    Used by the TUI to render the answer live, token by token.
    """
    if not chunks:
        yield "I couldn't find anything relevant to that in your indexed files."
        return

    model = _select_model(query, chunks)
    prompt = _build_prompt(query, chunks, history=history)

    stream = _client.generate(
        model=model,
        prompt=prompt,
        stream=True,
        options={
            "num_gpu": 99,
            "num_ctx": 4096,
        },
    )
    for chunk in stream:
        token = chunk.get("response", "")
        if token:
            yield token
