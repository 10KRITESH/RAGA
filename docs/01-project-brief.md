# 01 — Project Brief

## Project Name
RAGA

## What It Is
A local-first, privacy-preserving AI assistant that lets you ask natural language
questions about your entire Linux system — files, notes, code, screenshots, and
more — and always has an up-to-date answer, because it continuously watches your
filesystem and indexes changes in real time. No manual re-scanning, no cloud
dependency by default.

## Why Build It
Existing AI CLI tools (Claude Code, Aider, etc.) are reactive — they search live,
scoped to wherever you point them, with no memory between sessions. General file
search (fd/grep/locate) is fast but purely keyword-based, requiring you to
remember exact names. Neither solves the actual problem: "I vaguely remember
something about X somewhere on my system, and I want an instant, meaning-aware
answer, with sources, without my data leaving my machine."

RAGA closes that gap by combining:
- **Persistent, pre-built memory** — the index already exists before you ask,
  instead of scanning at query time.
- **Whole-system scope by default** — not limited to the folder you happen to be
  in.
- **Continuous, automatic freshness** — a background watcher reacts to file
  changes the moment they happen.
- **Local-only by default** — embeddings, storage, and inference all run on your
  machine; cloud models (Gemini, Groq) are strictly opt-in for answer generation
  only, never for indexing.

## Who It's For
- **Primary:** personal daily-driver tool for your own Linux setup (CachyOS,
  Hyprland, fish/foot workflow) — a "second brain" for your own machine.
- **Secondary:** a portfolio project that demonstrates a different class of
  engineering problem than your existing RAG projects (CodeLens, DocMind) —
  real-time incremental indexing, filesystem event handling, hybrid retrieval,
  and privacy-first architecture, rather than one-shot document RAG.

## Core Value Proposition
"Your entire computer, semantically searchable, and it never phones home — not
to OpenAI, not to Anthropic, not to anyone. If your wifi is off, it still
works."

## How It's Different From Similar Tools
| Tool | What it does | How RAGA differs |
|---|---|---|
| Claude Code / Aider / AI CLI tools | Reactive, on-demand file reading scoped to current task/directory, no persistent memory | Pre-indexed, whole-system scope, persistent across sessions |
| fd / grep / locate | Fast exact keyword/filename matching | Semantic (meaning-based) search — no need to remember exact wording |
| RAG-Anything (HKUDS) | Library for parsing complex multimodal *documents* you explicitly feed it (batch) | Continuously watches and indexes your *entire live filesystem* automatically (real-time), not a document-parsing library |

## High-Level Scope (subject to change — see Requirements doc for detail)
**In scope for v1:**
- Background daemon that watches selected directories and indexes changes in
  real time
- CLI for asking questions (`ask`, `chat`, `status`, `reindex`)
- Local embeddings + local LLM answer generation via Ollama
- Source citations (which file(s) an answer came from)
- Basic PDF and OCR (screenshot/image) content extraction

**Explicitly out of scope for v1** (candidates for later):
- Cloud LLM provider support (Gemini/Groq) as opt-in
- TUI chat interface
- Browser history / clipboard indexing
- Live system tools (RAM, processes, package queries)
- Walker/Vicinae launcher integration

## Success Criteria
- The tool can answer "where is X" and "what does X say" questions about files
  across multiple watched directories, correctly and with source paths.
- A newly created or edited file becomes queryable within seconds, with no
  manual re-index step.
- The entire query path (embed → retrieve → generate) works with network
  access disabled.
