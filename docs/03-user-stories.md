# 03 — User Stories

Format: As a [user], I want to [action], so that [benefit].
All stories are written from Spector's perspective as the sole user of RAGA.

## Epic: Indexing & Freshness

- US-1: As a user, I want the daemon to start automatically on login, so that
  indexing is always running without me having to remember to start it.
- US-2: As a user, I want a newly saved file to be searchable within seconds,
  so that I never have to manually trigger a re-index after normal work.
- US-3: As a user, I want deleted files to stop showing up in answers, so
  that I don't get pointed to content that no longer exists.
- US-4: As a user, I want to add a new directory to be watched, so that I can
  bring a new project or folder into scope without restarting everything.
- US-5: As a user, I want certain directories (e.g., `node_modules`, `.git`,
  build artifacts) excluded automatically, so that my index isn't flooded
  with noise I'll never query.
- US-6: As a user, I want unchanged files to be skipped during re-scans, so
  that indexing doesn't waste time/resources re-embedding the same content.

## Epic: Querying

- US-7: As a user, I want to ask "where is X" and get the correct file path,
  so that I don't have to remember exact filenames or locations.
- US-8: As a user, I want to ask a question about the *content* of a file
  ("how did I fix the libcava issue"), so that I can recall past problem-
  solving without digging through notes manually.
- US-9: As a user, I want every answer to show which file(s) it came from,
  so that I can verify the answer and jump straight to the source.
- US-10: As a user, I want to ask follow-up questions in a chat session, so
  that I don't have to restate context every time.
- US-11: As a user, I want a one-shot `ask` command for quick lookups, so
  that I can get an answer without entering an interactive session for
  simple questions.

## Epic: Operability & Trust

- US-12: As a user, I want to check the daemon's status (files indexed, last
  update, pending items), so that I can trust the index is actually current
  before relying on an answer.
- US-13: As a user, I want to manually force a re-index of a folder, so that
  I can recover from a missed event or bulk-import an existing folder for the
  first time.
- US-14: As a user, I want the daemon to survive a crash/restart without
  losing its index or requiring a full re-scan, so that I don't lose trust in
  the tool after a system hiccup.

## Epic: Privacy

- US-15: As a user, I want the entire ask/answer flow to work with no
  internet connection, so that I can trust my files never leave my machine.
- US-16: As a user, I want to be clearly warned when a query is about to use
  a cloud LLM provider, so that I never accidentally send private content off
  my machine.
- US-17: As a user, I want to explicitly opt in per-query (or per-session) to
  a cloud provider, so that cloud usage is always a deliberate choice, not a
  silent default.

## Epic: Content Coverage

- US-18: As a user, I want screenshots I've taken to be searchable via their
  OCR'd text, so that I can find something I remember seeing on screen but
  never saved as a file.
- US-19: As a user, I want PDFs (notes, papers, docs) to be indexed properly,
  so that I can ask questions about their content, not just their filenames.
- US-20: As a user, I want code files to be chunked in a way that respects
  function/class boundaries, so that answers about code aren't based on
  arbitrarily split fragments.

## Epic: Shell Integration / File Actions (v1.1)

- US-21: As a user, I want to say "open that pdf about federated learning"
  and have it open directly, so that I don't have to manually locate and
  open the file myself.
- US-22: As a user, I want to be asked for confirmation before a file is
  deleted or moved, so that a misidentified match can't destroy something by
  accident.
- US-23: As a user, I want deleted files to go to trash rather than being
  permanently removed, so that a mistaken delete is still recoverable.
- US-24: As a user, I want to be shown a list of candidates when my request
  is ambiguous ("delete that pdf" matching multiple files), so that I can
  pick the right one instead of the system guessing.

## Prioritization (for Development Plan reference)

**Must-have for v1:** US-1, US-2, US-3, US-6, US-7, US-8, US-9, US-11, US-12,
US-15, US-19
**Should-have for v1:** US-4, US-5, US-13, US-18
**Nice-to-have / later:** US-10, US-14, US-16, US-17, US-20 (TUI chat and
cloud provider stories depend on features explicitly deferred in the
Requirements doc)
**Planned for v1.1:** US-21, US-22, US-23, US-24 (shell integration / file
actions — see Requirements Section 2A)
