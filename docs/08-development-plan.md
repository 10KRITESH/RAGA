# 08 — Development Plan

This plan breaks the project into milestones → features → tasks, ordered so
that each milestone produces something runnable and testable, rather than
building all layers in parallel with nothing working end-to-end until the
very end.

Note (per the Project Brief's closing principle): this plan is a living
document. Expect the task breakdown — and possibly the architecture, API,
and requirements themselves — to shift once real implementation starts.

## Milestone 0 — Project Scaffolding
**Goal:** a working, empty skeleton — nothing functional yet, but the shape
of the project exists and runs.

- [ ] Initialize `pyproject.toml` with `uv`, set up folder structure
      (`watchers/`, `extractors/`, `ingestion/`, `storage/`, `core/`, `cli/`)
- [ ] Set up `config.py` — watched dirs, exclusions, model names (from
      Database Design's `watched_dirs`/`exclusions` tables, initially as a
      simple config file before DB-backed config exists)
- [ ] Basic `typer` app with a stub `raga status` command that just prints
      "not implemented yet"
- [ ] Confirm Ollama is reachable locally (basic health check script)

## Milestone 1 — Ingestion Pipeline (Read Path)
**Goal:** a file dropped into a watched folder gets embedded and stored —
no querying yet, just prove the write path works.

- [ ] Implement `FilesystemWatcher` using `watchdog`, emitting normalized
      `SourceEvent` objects
- [ ] Implement `TextExtractor` (plain text/code — simplest case first)
- [ ] Implement chunking (start naive/sliding-window; swap to Chonkie once
      pipeline is proven end-to-end)
- [ ] Implement `OllamaProvider.embed()`
- [ ] Set up SQLite `files` table + basic insert/update/delete logic
      (content-hash dedup per FR-4)
- [ ] Set up LanceDB `chunks` table + insert logic
- [ ] Manual test: create/edit/delete a `.txt` file, confirm rows appear/
      disappear correctly in both stores

## Milestone 2 — Query Path (CLI `ask`)
**Goal:** `raga ask "..."` returns a real, sourced answer.

- [ ] Implement `Retriever` — embed query, similarity search against LanceDB
- [ ] Implement `Answer Generator` — build prompt from retrieved chunks,
      call `OllamaProvider.generate()`
- [ ] Wire `ask()` Core Engine function per API Spec Section 1
- [ ] Implement `raga ask` CLI command, rendering answer + sources (per
      UI/UX Section 2)
- [ ] Manual test: ask a question about a file indexed in Milestone 1,
      confirm correct file is cited

**Checkpoint:** this is the first fully working slice — daemon watches,
CLI answers with sources. Everything after this is depth and polish.

## Milestone 3 — Operability
**Goal:** trust and control over what's indexed.

- [ ] Implement `status()` Core Engine function + `daemon_log` table writes
- [ ] Implement `raga status` CLI command
- [ ] Implement `reindex()` Core Engine function + `raga reindex` CLI command
      with progress output
- [ ] Implement `configure_watch()` / `configure_exclusion()` + persist to
      SQLite tables
- [ ] Package daemon as a systemd user service (mirroring the existing
      wallpaper-rotate service pattern)
- [ ] Manual test: kill and restart the daemon, confirm no data loss and no
      full re-index required (NFR-3)

## Milestone 4 — Content Coverage Expansion
**Goal:** move beyond plain text to the content types that make this
actually useful day-to-day.

- [ ] Implement `PDFExtractor` (PyMuPDF)
- [ ] Implement `ImageOCRExtractor` (pytesseract, reusing existing
      activity-logger pipeline logic)
- [ ] Swap naive chunker → Chonkie for text
- [ ] Add Tree-sitter based chunking for code files
- [ ] Manual test: index a PDF and a screenshot, confirm both are queryable

## Milestone 5 — Retrieval Quality
**Goal:** answers are actually good, not just present.

- [ ] Integrate `bge-reranker-base` into the retrieval path (post-retrieval,
      pre-generation)
- [ ] Add hybrid search (vector + full-text via LanceDB) to `Retriever`
- [ ] Tune chunk size/overlap based on manual quality testing
- [ ] Route code-context queries to `qwen2.5-coder`, general queries to
      `llama3.2:3b` (per System Design's provider routing)

## Milestone 6 — Conversational Interface (TUI)
**Goal:** `raga chat` becomes a real, sustained interaction surface.

- [ ] Scaffold Textual app with chat pane / sources panel / status bar
      layout (per UI/UX Section 3)
- [ ] Implement multi-turn `Session` object, wire into `ask(query, session)`
- [ ] Implement source preview on selection (Enter to preview, per UI/UX)
- [ ] Manual test: multi-turn conversation with follow-up questions retains
      context correctly

## Milestone 7 (v1 Release Candidate)
**Goal:** everything in Requirements' "Must-have for v1" / "Should-have for
v1" list (User Stories doc) is functional and stable.

- [ ] Full pass against User Stories Must-have list (US-1, 2, 3, 6, 7, 8, 9,
      11, 12, 15, 19)
- [ ] Full pass against Should-have list (US-4, 5, 13, 18)
- [ ] Verify NFR-4 (privacy): full ask→answer flow works with network
      disabled
- [ ] Write README with setup instructions, airplane-mode privacy demo
- [ ] Resolve or explicitly punt open questions from Requirements doc
      (index size limits, failed-extraction handling, redaction)

## Milestone 8 (v1.1) — Shell Integration / File Actions
**Goal:** implement the deferred action capability (Requirements Section 2A).

- [ ] Implement `Action Router` — detect action intent in queries
- [ ] Implement `open` action via `xdg-open` (low-risk, no confirmation
      needed)
- [ ] Implement `delete` action via `send2trash` (trash, not permanent —
      FR-22)
- [ ] Implement confirmation flow for destructive actions (FR-21)
- [ ] Implement disambiguation flow for multiple candidate matches (FR-23)
- [ ] Wire `execute_action()` Core Engine function + CLI/TUI confirmation UI
      (per UI/UX action command examples)
- [ ] Manual test: ambiguous delete request correctly lists candidates and
      requires explicit confirmation before touching the filesystem

## Milestone 9+ (Future / Not Yet Planned in Detail)
- Cloud provider support (Gemini/Groq) as explicit opt-in (FR-17/FR-18)
- Live system-state tool-calling (RAM, processes, packages)
- Browser history / clipboard indexing
- Walker/Vicinae launcher integration (likely triggers the deferred HTTP API
  from API Spec Appendix)
- Redaction pass before embedding, if prioritized

## How to Use This Plan
- Work top to bottom, but treat each milestone's checkbox list as a
  starting point, not a contract — update it as reality diverges from the
  plan.
- Milestone 2 is the meaningful "it actually works" checkpoint — resist the
  urge to perfect Milestones 0-1 before reaching it.
- Revisit the linked docs (Requirements, User Stories, System Design) as
  design decisions shift during implementation, so they stay accurate rather
  than becoming stale documentation.
