# RAGA — System Setup Checklist

Everything needed on your CachyOS (Arch-based) machine before/while building
RAGA, grouped by category.

## 1. System-Level (via pacman)

```bash
sudo pacman -S python python-pip tesseract tesseract-data-eng sqlite
```

| Package | Why |
|---|---|
| `python` | Python 3.12+ runtime |
| `tesseract` + `tesseract-data-eng` | OCR engine for image/screenshot extraction (you likely already have this from the activity logger) |
| `sqlite` | Metadata DB (usually already present on Arch by default, but confirm) |

`systemd` (for the daemon as a user service) is already part of your base
system — nothing to install.

## 2. Ollama + Models

If not already fully set up (you already run Ollama daily, so this may just
be pulling new models):

```bash
# Ollama itself (skip if already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Models needed for RAGA specifically
ollama pull nomic-embed-text      # embeddings
ollama pull llama3.2:3b           # general Q&A generation (default)
ollama pull qwen2.5-coder:7b      # code-context generation (you may already have this)
```

## 3. Python Package Manager

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

`uv` will manage everything below via `pyproject.toml` — you won't
individually `pip install` each one, but here's what will go in there:

## 4. Python Dependencies (installed via `uv add`, for reference)

| Package | Purpose |
|---|---|
| `watchdog` | Filesystem watching (inotify wrapper) |
| `lancedb` | Vector database |
| `chonkie` | Semantic text chunking |
| `tree-sitter` + `tree-sitter-languages` | Structure-aware code chunking |
| `ollama` | Python client for Ollama (embeddings + generation) |
| `pymupdf` | PDF text extraction |
| `pytesseract` | Python wrapper around the `tesseract` binary |
| `typer` | CLI framework |
| `textual` | TUI framework (for `raga chat`) |
| `sentence-transformers` | Runs `bge-reranker-base` locally for reranking |
| `sqlmodel` (optional) | Nicer ORM layer over SQLite, if you don't want raw `sqlite3` |
| `send2trash` | v1.1 — safe delete-to-trash for file actions |
| `pydantic` | Data validation for Core Engine request/response objects (Answer, SourceRef, etc.) |

These get added via:
```bash
uv add watchdog lancedb chonkie tree-sitter tree-sitter-languages ollama \
       pymupdf pytesseract typer textual sentence-transformers pydantic
```

(`send2trash` added later when you reach Milestone 8 / v1.1.)

## 5. Optional / Later (v1.1+)

| Package | Purpose | When needed |
|---|---|---|
| `google-generativeai` | Gemini API client | If/when opt-in cloud provider support is built |
| `groq` | Groq API client | Same — opt-in cloud generation |
| `fastapi` + `uvicorn` | HTTP layer | Only if you move to the deferred multi-client architecture (Walker integration, web UI) |

## 6. Verify Before Starting Milestone 0

```bash
python --version        # should be 3.12+
uv --version
ollama list              # confirms nomic-embed-text, llama3.2:3b, qwen2.5-coder present
tesseract --version
sqlite3 --version
```

## 7. Hardware Note

Your RTX 3050 (4GB VRAM) comfortably handles `nomic-embed-text` and
`llama3.2:3b`. `qwen2.5-coder:7b` and `bge-reranker-base` running
simultaneously may be tight on VRAM — worth watching GPU memory during
Milestone 5 (reranker integration) and falling back to CPU for the reranker
if needed, since it's a much smaller model than your LLMs and CPU inference
for it should still be fast enough for personal-scale use.
