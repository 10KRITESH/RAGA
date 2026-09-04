# 05 — System Design

## 1. Architectural Style

RAGA is a **local, layered, plugin-based system** — no client-server network
architecture in v1 (everything runs as local processes on one machine). Each
layer depends only on the layer directly below it, so new capabilities
(file types, data sources, LLM providers) are added by implementing an
interface, not modifying core logic.

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     INTERFACE LAYER                       │
│         CLI (raga ask/status/reindex)                     │
│         TUI (raga chat)                                    │
│         [later: Walker plugin, web UI, voice]               │
└───────────────────────┬───────────────────────────────────┘
                         │ calls
┌───────────────────────▼───────────────────────────────────┐
│                    CORE ENGINE                              │
│  - Query Router   - Retriever   - Reranker                  │
│  - Answer Generator   - Action Router (v1.1)                 │
└───────────────────────┬───────────────────────────────────┘
                         │ reads/writes
┌───────────────────────▼───────────────────────────────────┐
│                    STORAGE LAYER                             │
│   Vector DB (LanceDB)   +   Metadata DB (SQLite)              │
└───────────────────────▲───────────────────────────────────┘
                         │ writes
┌───────────────────────┴───────────────────────────────────┐
│                  INGESTION PIPELINE                          │
│   Extractor Registry → Chunker → Embedder                    │
└───────────────────────┬───────────────────────────────────┘
                         │ triggers on
┌───────────────────────▼───────────────────────────────────┐
│                  SOURCE WATCHERS (pluggable)                 │
│   Filesystem watcher (Watchdog)                               │
│   [later: browser history, clipboard]                          │
└─────────────────────────────────────────────────────────────┘
```

## 3. Component Responsibilities

### 3.1 Source Watchers
- Detect file create/modify/delete/move events via `watchdog` (inotify).
- Normalize events into a common `SourceEvent(path, event_type, source_type)`
  shape and push them onto an `asyncio.Queue` consumed by the Ingestion
  Pipeline.
- Interface-based (`SourceWatcher` ABC) so new sources (browser history,
  clipboard) can be added later without touching the pipeline.

### 3.2 Ingestion Pipeline
- **Extractor Registry** — selects the right content extractor per file type
  (plain text, PDF via PyMuPDF, image via Tesseract OCR). Interface-based
  (`Extractor` ABC with `can_handle()`/`extract()`), extensible per file type.
- **Chunker** — splits extracted text into retrieval-sized chunks. Text uses
  Chonkie (semantic chunking); code uses Tree-sitter (structure-aware,
  function/class-boundary-respecting).
- **Embedder** — wraps the embedding provider (Ollama / nomic-embed-text by
  default) behind one interface, so swapping models later doesn't touch
  calling code.
- Runs as part of the daemon process, consuming events from the watcher
  queue asynchronously (non-blocking).

### 3.3 Storage Layer
- **Vector DB (LanceDB)** — embedded, no separate server process. Stores
  chunk text, embedding vector, and a reference to metadata. Supports hybrid
  (vector + full-text) search natively.
- **Metadata DB (SQLite)** — stores per-file records: path, content hash,
  mtime, last indexed time, source type. Used for dedup (skip unchanged
  files), stale-entry cleanup on delete, and powering `raga status`.
- These two stores are deliberately separate: LanceDB is optimized for
  similarity search, SQLite is optimized for exact structured lookups —
  each does the job it's actually good at.

### 3.4 Core Engine
- **Query Router** — determines how to answer a query. Distinguishes
  content/location questions (→ Retriever) from live-state questions (→
  future live-tool calls, deferred) and from action-intent queries (→ Action
  Router, v1.1).
- **Retriever** — embeds the query, performs hybrid search against LanceDB,
  returns candidate chunks with metadata.
- **Reranker** — re-scores retrieved candidates (bge-reranker-base) to
  improve precision before they're passed to the generator. Included in v1
  scope given retrieval quality is central to the product's usability.
- **Answer Generator** — builds the final prompt from reranked chunks +
  query, calls the selected LLM provider (Ollama by default; general model
  for text, code model routed in when context is source code), returns the
  answer plus the source file paths used.
- **Action Router (v1.1)** — detects action intent (open/delete/move) in a
  query once a confident file match exists, applies the confirmation/trash
  rules defined in Requirements Section 2A, and executes via OS-level calls
  (`xdg-open`, `send2trash`).

### 3.5 Interface Layer
- **CLI (Typer)** — thin layer calling Core Engine functions directly
  in-process for `ask`, `status`, `reindex`.
- **TUI (Textual)** — used for `chat`; maintains conversation state across
  turns, renders the chat pane / sources panel / status bar described in the
  UI/UX spec, and calls the same Core Engine functions as the CLI.
- Both interfaces call the Core Engine directly (in-process function calls)
  in v1 — no HTTP layer. This keeps the architecture simple while there's
  only one machine and one set of interfaces to serve.

## 4. Process Model

Two independent OS-level processes, coordinating only through shared on-disk
storage:

```
┌──────────────────────────┐
│  Daemon (systemd user     │  Always running. Owns: Source Watchers,
│  service)                  │  Ingestion Pipeline. Writes to Storage Layer.
└──────────────────────────┘
              │
              ▼
      ~/.local/share/raga/
        ├── lancedb/          (vector store)
        └── metadata.sqlite   (SQLite metadata)
              ▲
              │
┌──────────────────────────┐
│  CLI / TUI (on-demand)     │  Invoked manually. Owns: Core Engine (query
│                             │  side), Interface Layer. Reads from Storage
└──────────────────────────┘  Layer, does not write except via Action
                                Router (v1.1, filesystem writes only, not
                                storage writes).
```

This separation means the daemon can be restarted, crash, or be updated
without interrupting an in-progress `chat` session, and vice versa — they
never block each other, only share the on-disk stores.

## 5. Extensibility Points (by design)

| Want to add... | Implement... | Touches core logic? |
|---|---|---|
| New file type support | New `Extractor` | No |
| New data source (e.g. browser history) | New `SourceWatcher` | No |
| New embedding/LLM provider | New `LLMProvider` | No |
| New interface (e.g. Walker plugin) | New Interface Layer client calling existing Core Engine functions | No |

## 6. Provider Abstraction (LLM/Embeddings)

```python
class LLMProvider(ABC):
    def embed(self, text: str) -> list[float]: ...
    def generate(self, prompt: str) -> str: ...

class OllamaProvider(LLMProvider): ...   # default, always available, local
class GeminiProvider(LLMProvider): ...   # opt-in, v1.1+, generation only
class GroqProvider(LLMProvider): ...     # opt-in, v1.1+, generation only
```

Design rule (ties back to privacy positioning in the Project Brief):
**embedding provider stays local (Ollama) always** — only the generation
provider is ever configurable to a cloud option, and only with explicit
per-query/per-session opt-in and visible warning (FR-17/FR-18 in
Requirements).

## 7. Key Design Decisions & Rationale

| Decision | Rationale |
|---|---|
| No HTTP server in v1 | Single machine, single set of interfaces (CLI+TUI) — in-process calls are simpler and faster; HTTP layer deferred to a possible v2 if multiple concurrent clients (e.g. Walker) are added |
| LanceDB over Chroma | Native hybrid search, better suited to concurrent daemon-write / CLI-read access pattern |
| Separate metadata DB (SQLite) instead of storing everything in the vector DB | Structured lookups (dedup, stale cleanup, status reporting) are a poor fit for a vector store's query model |
| Reranker included in v1 | Retrieval quality is the core product experience — deferring it risks a weak first impression |
| Two independent processes (daemon + CLI/TUI) sharing only disk state | Avoids coupling interface responsiveness to indexing load, and vice versa |

## 8. Out of Scope for This Design (deferred)

- FastAPI-backed service layer (only needed once multiple concurrent clients
  exist, e.g. a future Walker integration or web UI).
- Live system-state tool-calling (RAM/process queries) — architecturally
  would live inside the Query Router as a new branch, not designed in detail
  yet.
- Multi-machine / remote access — out of scope entirely per Requirements.
