# 07 — API Specification

RAGA has no network-facing API in v1 (see System Design Section 3.5 — CLI and
TUI call the Core Engine directly, in-process). This document specifies that
**internal function-level API** as the contract between the Interface Layer
and the Core Engine, since it serves the same purpose an HTTP spec would in a
networked product. A deferred HTTP API sketch is included as an appendix for
the possible future phase where multiple concurrent clients exist.

## 1. Core Engine API (in-process, v1)

All functions are called directly by the CLI (Typer) and TUI (Textual) — no
serialization/network boundary in v1, so requests/responses are plain Python
objects, not JSON payloads.

### `ask(query: str, session: Session | None = None) -> Answer`
Primary query entrypoint. Used by both `raga ask` (one-shot, `session=None`)
and `raga chat` (multi-turn, `session` carries prior turns).

**Input:**
| Field | Type | Required | Description |
|---|---|---|---|
| `query` | str | Yes | Natural language question |
| `session` | Session \| None | No | Conversation context for multi-turn chat |

**Output — `Answer`:**
| Field | Type | Description |
|---|---|---|
| `text` | str | Generated answer |
| `sources` | list[SourceRef] | Files the answer was derived from |
| `provider_used` | str | e.g. `ollama`, `gemini` — surfaced for transparency (FR-18) |
| `action` | ActionResult \| None | Populated only if query had action intent (v1.1) |

**`SourceRef`:**
| Field | Type | Description |
|---|---|---|
| `file_path` | str | Absolute path |
| `snippet` | str | Retrieved chunk excerpt |
| `score` | float | Relevance score (post-rerank) |

**Errors:**
- `NoResultsFound` — retrieval returned nothing above relevance threshold;
  CLI/TUI should render "I couldn't find anything about that."
- `ProviderUnavailable` — configured LLM provider unreachable (e.g. Ollama
  not running); CLI/TUI should render a clear setup hint, not a stack trace.

---

### `status() -> DaemonStatus`
Backs `raga status`.

**Output — `DaemonStatus`:**
| Field | Type | Description |
|---|---|---|
| `daemon_running` | bool | Whether the daemon process is alive |
| `pid` | int \| None | Daemon process ID, if running |
| `watched_dirs` | list[str] | Currently watched directories |
| `files_indexed` | int | Count from `files` table where `status = 'indexed'` |
| `files_failed` | int | Count from `files` table where `status = 'failed'` |
| `pending_queue_size` | int | Items waiting in the ingestion queue |
| `last_indexed_at` | timestamp \| None | Most recent successful index event |

---

### `reindex(path: str, force: bool = False) -> ReindexHandle`
Backs `raga reindex`. Triggers indexing of a new or existing directory.

**Input:**
| Field | Type | Required | Description |
|---|---|---|---|
| `path` | str | Yes | Directory to index |
| `force` | bool | No | If true, re-index even unchanged files (bypasses content-hash dedup) |

**Output — `ReindexHandle`:**
| Field | Type | Description |
|---|---|---|
| `job_id` | str | Identifier for tracking progress |
| `total_files` | int | Files discovered to process |

Progress is polled via `reindex_progress(job_id)` for the CLI's progress bar
(Section 2 of UI/UX spec).

---

### `configure_watch(path: str, action: Literal["add","remove"]) -> None`
Adds or removes a directory from the watch scope (persists to `watched_dirs`
table).

### `configure_exclusion(pattern: str, action: Literal["add","remove"]) -> None`
Adds or removes an exclusion pattern (persists to `exclusions` table).

---

### v1.1 — `execute_action(action: ActionResult, confirmed: bool) -> ActionOutcome`
Executes a file action (open/delete/move) identified by the Action Router.
Called by the Interface Layer only after the confirmation flow described in
UI/UX Section 2 has resolved.

**Input:**
| Field | Type | Required | Description |
|---|---|---|---|
| `action` | ActionResult | Yes | The pending action (type + target file) returned from `ask()` |
| `confirmed` | bool | Yes | Must be true for destructive actions (delete/move); ignored for open |

**Output — `ActionOutcome`:**
| Field | Type | Description |
|---|---|---|
| `success` | bool | Whether the action completed |
| `message` | str | Human-readable result (e.g. "Moved to trash") |

## 2. Provider Interface (implemented by each LLM backend)

This is the contract every `LLMProvider` implementation must satisfy (see
System Design Section 6) — relevant here because it's the extension point
external contributors/future-you would implement against.

```python
class LLMProvider(ABC):
    def embed(self, text: str) -> list[float]:
        """Returns an embedding vector for the given text."""

    def generate(self, prompt: str) -> str:
        """Returns a generated text response for the given prompt."""
```

Implementations: `OllamaProvider` (default), `GeminiProvider` (v1.1, opt-in),
`GroqProvider` (v1.1, opt-in).

## 3. Appendix — Deferred HTTP API Sketch (future phase)

If a networked phase is built (see System Design Section 8 — needed only once
multiple concurrent clients exist, e.g. a Walker launcher integration or web
UI), the Core Engine functions above map directly to HTTP endpoints, bound to
`127.0.0.1` only (never exposed beyond localhost), consistent with existing
local-AI-tooling convention:

| Method | Endpoint | Maps to |
|---|---|---|
| POST | `/ask` | `ask(query, session)` |
| GET | `/status` | `status()` |
| POST | `/reindex` | `reindex(path, force)` |
| GET | `/reindex/{job_id}` | `reindex_progress(job_id)` |
| POST | `/config/watch` | `configure_watch(path, action)` |
| POST | `/config/exclusion` | `configure_exclusion(pattern, action)` |
| POST | `/action/execute` | `execute_action(action, confirmed)` |

No authentication is planned for this layer since it would be bound to
localhost only, single-user, single-machine — consistent with the
Requirements doc's explicit exclusion of multi-user/remote access.
