<div align="center">

# 🧠 RAGA — Local-First Real-Time Desktop AI Assistant

**Continuous Filesystem Watcher · Hybrid Vector Search · Cross-Encoder Reranker · Offline Local LLM**

RAGA transforms your entire computer into a privacy-preserving, semantically searchable second brain. It continuously indexes files, documents, source code, and images in real time using local embeddings and serves answers via an OpenCode Terminal UI (SolidJS / OpenTUI) and high-speed CLI.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![Bun](https://img.shields.io/badge/Bun-v1.2+-000000?style=flat-square&logo=bun&logoColor=white)](https://bun.sh)
[![LanceDB](https://img.shields.io/badge/LanceDB-Vector_DB-000000?style=flat-square&logo=databricks&logoColor=white)](https://lancedb.com)
[![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-FFFFFF?style=flat-square&logo=ollama&logoColor=black)](https://ollama.com)
[![SolidJS](https://img.shields.io/badge/SolidJS-OpenTUI-2C4F7C?style=flat-square&logo=solid&logoColor=white)](https://www.solidjs.com)
[![SQLite](https://img.shields.io/badge/SQLite-Metadata-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

</div>

---

## 📸 Architecture & Workflow

```
   Continuous Filesystem Events (Create / Modify / Delete / Move)
                                │
                                ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                    Watchdog Daemon                          │
  │                                                             │
  │  1. Inotify Event Debouncer (skips duplicates & temp files) │
  │  2. SQLite Metadata Check (MD5 Content Hash Deduplication)  │
  │  3. Extractor Registry (PDF, Tree-sitter, OCR, Markdown)    │
  │  4. Semantic Chunker (Chonkie + AST structure preservation) │
  │  5. Local Embedder (Ollama nomic-embed-text: 768-dim)       │
  │  6. Incremental Vector Storage (Embedded LanceDB)           │
  └─────────────────────────────┬───────────────────────────────┘
                                │ writes to disk
                                ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                   Embedded Storage Layer                    │
  │                                                             │
  │   • ~/.local/share/raga/lancedb/     (Vector Embeddings)    │
  │   • ~/.local/share/raga/meta.sqlite  (File Metadata & Hash) │
  └─────────────────────────────┬───────────────────────────────┘
                                │ queried by
                                ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                   Hybrid Query Engine                       │
  │                                                             │
  │  Pass 1: Query Intent Classifier (FS / Location / Content)  │
  │  Pass 2: Hybrid Retrieval (Cosine Vector + BM25 FTS + Path) │
  │  Pass 3: Weighted Reciprocal Rank Fusion (RRF)              │
  │  Pass 4: Cross-Encoder Semantic Reranker (ms-marco-MiniLM)  │
  │  Pass 5: Dynamic Code/General Model Routing                 │
  │  Pass 6: Local Ollama Generation (Streaming Answer)         │
  └─────────────────────────────┬───────────────────────────────┘
                                │
         ┌──────────────────────┴──────────────────────┐
         ▼                                             ▼
┌──────────────────────────────┐              ┌──────────────────┐
│     OpenCode Terminal UI     │              │     Fast CLI     │
│   (SolidJS / OpenTUI / Bun)  │              │   (Python/Typer) │
│  • Floating Slash Menu       │              │  • raga ask      │
│  • Model Switcher (/model)   │              │  • raga status   │
│  • Chunk Preview Sidebar     │              │  • raga reindex  │
│  • History & Clipboard Toast │              │  • raga chat     │
└──────────────────────────────┘              └──────────────────┘
```

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Continuous Real-Time Watcher** | Inotify/Watchdog daemon indexes newly saved, edited, or moved files within milliseconds. |
| **Hybrid Retrieval Engine** | Merges 768-dim semantic embeddings, BM25 full-text search, and path/metadata matching via Weighted Reciprocal Rank Fusion (RRF). |
| **Cross-Encoder Reranking** | Micro-second neural reranking with `ms-marco-MiniLM-L-6-v2` guarantees pinpoint source precision. |
| **100% Offline & Private** | Embeddings, storage, reranking, and inference execute entirely locally on your hardware. Zero telemetry. |
| **OpenCode Terminal UI** | Sleek TUI built with SolidJS, OpenTUI, and Bun featuring live telemetry, source inspections, and prompt switching. |
| **Dynamic Model Routing** | Automatically routes code queries to code-specialized models (`qwen2.5-coder`) and natural queries to general LLMs. |
| **AST & Multi-Modal Extraction** | Tree-sitter code parser, PyMuPDF document extractor, Chonkie semantic chunker, and Tesseract OCR engine. |
| **Terminal Keybindings & History** | Command history cycling ($\uparrow$/$\downarrow$), multiline prompts (`Shift+Enter`), native clipboard (`Ctrl+V`), and top-right copy popups. |

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **TUI Interface** | SolidJS + OpenTUI (Bun) | High-performance terminal GUI with reactive state and animations |
| **CLI Runtime** | Python 3.11+ / Typer + Rich | Instant command-line query and admin tools |
| **Vector Database** | LanceDB (Embedded) | Serverless, disk-backed columnar vector storage with native hybrid search |
| **Metadata Database** | SQLite 3 | Content hashing (MD5), mtime tracking, and deduplication records |
| **Local Embeddings** | Ollama (`nomic-embed-text`) | Local 768-dimensional dense vector generation |
| **Inference Models** | Ollama (`qwen2.5:3b`, `qwen2.5-coder`, `llama3.2`, `llama2`) | Local natural language and code generation |
| **Reranker** | Sentence-Transformers (`CrossEncoder`) | ms-marco-MiniLM neural reranker running on CPU |
| **File Watcher** | Watchdog (Inotify) | Real-time background filesystem event monitor |
| **Code Parser** | Tree-sitter | Syntax-aware structural chunking for 20+ programming languages |
| **Document Parser** | PyMuPDF (fitz) | Fast PDF text and metadata extraction |
| **OCR Engine** | Tesseract OCR + Pillow | Image and screenshot text extraction |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+** and [`uv`](https://docs.astral.sh/uv/) package manager
- **Bun** (v1.2+) runtime for the OpenCode TUI
- **Ollama** installed and running locally
- **Tesseract OCR** (for image and screenshot ingestion):
  ```bash
  # Arch / CachyOS
  sudo pacman -S tesseract tesseract-data-eng
  
  # Ubuntu / Debian
  sudo apt-get install tesseract-ocr
  ```

### 1. Clone Repository

```bash
git clone https://github.com/10KRITESH/RAGA.git
cd RAGA
```

### 2. Set Up Python Virtual Environment

```bash
# Create and sync virtual environment with uv
uv sync
```

### 3. Pull Required Ollama Models

```bash
# Local embedding model
ollama pull nomic-embed-text

# Local generation models (choose one or more)
ollama pull qwen2.5:3b
ollama pull qwen2.5-coder:7b
ollama pull llama3.2:3b
```

### 4. Configure Watched Directories

Edit `config.py` to specify the directories you want RAGA to continuously watch and index:

```python
WATCHED_DIRS = [
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Desktop"),
]
```

### 5. Start Background Ingestion Daemon

```bash
uv run python daemon.py
```

---

## 💻 Usage

### Launch the OpenCode Terminal UI (TUI)

```bash
cd tui-opentui
bun install
bun run dev
```

### Using the Fast Command Line Interface (CLI)

```bash
# Ask a direct question about your files
uv run python -m cli.main ask "Where are my ethical hacking notes?"

# Find files matching a topic or project
uv run python -m cli.main ask "List all assignments in SEM VII CC"

# View system telemetry and indexing stats
uv run python -m cli.main status

# Force a complete re-indexing of all watched folders
uv run python -m cli.main reindex
```

---

## ⌨️ TUI Keybindings & Slash Commands

### Keybindings

| Keybinding | Action |
|------------|--------|
| **`Enter`** | Submit prompt query |
| **`Shift + Enter`** | Insert newline for multiline prompt |
| **`↑ / ↓`** | Scroll through prompt command history |
| **`Ctrl + V`** | Paste text from system clipboard (Wayland / X11) |
| **`Ctrl + C`** | Copy selected text (or prompt) with toast confirmation |
| **`Ctrl + P`** | Open Command Palette (Models, Themes, Agent Modes) |
| **`Tab`** | Cycle Agent Mode (`Build`, `Query`, `Shell`, `Ask`) |
| **`1 – 5`** | Inspect source citation chunk in the sidebar |
| **`Ctrl + L`** | Clear active chat session |
| **`Esc`** | Interrupt running LLM generation / Close palette |

### Slash Commands

Type `/` in the prompt input to activate the autocomplete menu:

- `/model` — Switch active Ollama LLM model on the fly
- `/agents` — Change active agent mode (`Build`, `Query`, `Shell`, `Ask`)
- `/themes` — Switch theme (`opencode`, `nord`, `tokyonight`, `catppuccin`, `matrix`, `dracula`, `gruvbox`)
- `/status` — View indexing health, failure count, and file stats
- `/copy` — Copy full conversation transcript to clipboard
- `/clear` — Reset conversation state and session title
- `/exit` — Gracefully close RAGA

---

## 📄 Supported Formats

| Format | Extensions | Extraction Method |
|--------|------------|-------------------|
| **Source Code** | `.py`, `.js`, `.ts`, `.tsx`, `.rs`, `.go`, `.c`, `.cpp`, `.java`, `.kt`, `.lua`, `.zig`, `.sh`, `.sql`, `.html`, `.css` | Tree-sitter AST & token chunking |
| **Documents** | `.pdf` | PyMuPDF text & structure extractor |
| **Markdown / Text** | `.md`, `.markdown`, `.txt`, `.rst` | Chonkie semantic boundary chunker |
| **Structured Data** | `.json`, `.yaml`, `.yml`, `.toml`, `.csv` | Specialized structured text parsers |
| **Images & Screenshots** | `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.tiff` | Tesseract OCR engine |

---

## 📂 Project Structure

```
RAGA/
├── core/                       # Core Retrieval, Reranking & LLM Generation
│   ├── engine.py               # Main public query router
│   ├── retriever.py            # Hybrid Search (Vector + BM25 + Path RRF)
│   ├── reranker.py             # CrossEncoder neural reranker
│   ├── generator.py            # Ollama answer synthesis & stream handler
│   ├── query_classifier.py     # Intent classifier (filesystem / location / content)
│   ├── filesystem_engine.py    # Zero-LLM directory and file location resolver
│   ├── reindex_engine.py       # Full batch reindexer
│   └── status_engine.py        # System health and index telemetry
├── ingestion/                  # Content Extraction & Chunking Pipeline
│   ├── watcher.py              # Inotify filesystem event monitor
│   ├── extractors/             # File extractors (PyMuPDF, Tree-sitter, OCR)
│   ├── chunker.py              # Semantic and AST code chunking
│   └── embedder.py             # Ollama embedding wrapper
├── storage/                    # Database & Persistence
│   ├── vector_store.py         # LanceDB table setup and vector index
│   └── metadata_db.py          # SQLite metadata and content hash records
├── tui-opentui/                # OpenCode Terminal User Interface
│   ├── src/
│   │   ├── app.tsx             # Main SolidJS TUI application & layout
│   │   ├── bridge.ts           # Subprocess bridge to Python Core Engine
│   │   ├── theme/              # Color themes (Nord, Tokyo Night, Dracula, etc.)
│   │   ├── components/         # Message cards, Sidebar, Slash menu, Palette
│   │   └── util/               # Wayland/X11 clipboard and terminal utils
│   └── package.json            # Bun package definition
├── cli/                        # Typer CLI Entry Point
│   └── main.py                 # CLI commands (ask, status, reindex, chat)
├── daemon.py                   # Background continuous watcher daemon
├── config.py                   # System configuration & watched paths
└── README.md
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

**Built by [Kritesh Goud](https://github.com/10KRITESH)**

</div>
