# 02 — Requirements / PRD

## 1. Functional Requirements

### 1.1 Indexing
- FR-1: The system MUST watch a configurable list of directories for file
  create, modify, delete, and move events.
- FR-2: On file create/modify, the system MUST extract text content, chunk it,
  generate embeddings, and store them in the vector database within a few
  seconds of the change.
- FR-3: On file delete/move, the system MUST remove or update the
  corresponding vector DB entries so stale results are never returned.
- FR-4: The system MUST avoid re-embedding unchanged files (content-hash based
  dedup).
- FR-5: The system MUST support content extraction for: plain text, code
  files, PDFs, and images (via OCR).
- FR-6: The system MUST maintain a metadata record per indexed file: path,
  content hash, last modified time, last indexed time, source type.

### 1.2 Querying
- FR-7: The user MUST be able to ask a natural language question and receive
  an answer grounded in indexed content.
- FR-8: Every answer MUST include the source file path(s) it was derived from.
- FR-9: The system MUST support a one-shot query mode (`ask`) and a
  multi-turn conversational mode (`chat`).
- FR-10: The system MUST support "where is X" style path/location queries,
  not just content-based questions.
- FR-11: The retrieval step MUST use semantic (embedding-based) search, not
  purely keyword matching.

### 1.3 Operability
- FR-12: The user MUST be able to check daemon health and indexing status
  (`status`) — e.g., files indexed, last update time, pending queue size.
- FR-13: The user MUST be able to manually trigger indexing of a new
  directory (`reindex`).
- FR-14: The user MUST be able to configure which directories are watched and
  which are explicitly excluded.
- FR-15: The daemon MUST run as a background service (systemd user service)
  independent of the CLI process.

### 1.4 Privacy & Local-First
- FR-16: All embedding generation and vector storage MUST occur locally by
  default, with no network calls required for indexing or querying.
- FR-17: Cloud LLM providers (e.g., Gemini, Groq) MUST be opt-in only, and
  MUST be used solely for answer generation — never for embeddings or
  indexing.
- FR-18: When a cloud provider is used for a query, the system MUST make this
  visible to the user (not a silent fallback).

## 2. Non-Functional Requirements

- NFR-1 (Performance): A newly created/modified file should become queryable
  within seconds under normal system load.
- NFR-2 (Resource usage): Indexing must not saturate CPU/GPU to the point of
  disrupting normal desktop use — batching/throttling should be considered for
  large bulk changes (e.g., git checkout touching thousands of files).
- NFR-3 (Reliability): The daemon should recover gracefully from crashes
  without corrupting the vector DB or metadata store, and should resume
  watching without requiring a full re-index.
- NFR-4 (Privacy): No file content or embeddings should leave the machine
  unless the user has explicitly opted into a cloud provider for that query.
- NFR-5 (Portability): The system should run on the user's actual daily
  environment (CachyOS / Arch-based Linux, Hyprland) without requiring
  containers or VMs for core operation.
- NFR-6 (Extensibility): Adding a new content extractor, source watcher, or
  LLM provider should require implementing one interface, not modifying core
  pipeline logic.

## 3. Explicitly Out of Scope (v1)

- Cloud LLM provider integration (Gemini/Groq) — planned for a later phase,
  not v1.
- TUI chat interface — v1 ships CLI only (`typer`), TUI is a planned upgrade.
- Browser history / clipboard / shell history indexing.
- Live system tools (RAM usage, running processes, package queries via
  tool-calling).
- Walker/Vicinae launcher integration.
- Multi-user support — this is a single-user, single-machine tool.
- Mobile or remote access — local machine only.
- Automatic file actions (move/rename/delete via natural language) — v1 is
  read-only/query-only, no write actions on the filesystem.

## 4. Assumptions

- Ollama is already installed and running locally with required models
  pulled (embedding + generation).
- The user has basic familiarity with systemd user services and CLI tools.
- The initial watched directory set is small/curated (e.g., ~/Documents,
  ~/Projects), not the entire root filesystem.

## 5. Open Questions (to revisit during development)

- What is the practical upper bound on index size before LanceDB query
  latency becomes noticeable at personal scale?
- How should the system handle files that fail extraction (corrupted PDFs,
  unreadable images) — skip silently, log, or surface to `status`?
- Should redaction (secret/API-key scrubbing before embedding) be a v1
  requirement given the privacy positioning, or acceptable to defer?
