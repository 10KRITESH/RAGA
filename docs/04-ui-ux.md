# 04 — UI/UX Specification

RAGA has no traditional GUI. Its interface surface is a CLI (for discrete
commands) plus a TUI (for the sustained `chat` experience). This document
specifies command structure, output layout, and TUI screen design in place of
wireframes.

## 1. Interface Surfaces

| Surface | Tool | Used for |
|---|---|---|
| CLI | Typer | One-shot commands: `ask`, `status`, `reindex`, `open`/`delete` actions (v1.1) |
| TUI | Textual | Sustained interaction: `chat` |

## 2. CLI Commands

### `raga ask "<question>"`
One-shot query. Prints the answer, followed by a "Sources" section listing
file paths (and optionally a short snippet per source).

```
$ raga ask "where's my caelestia config"

RAGA> Your Caelestia config lives at ~/.config/caelestia/. The main
      shell config is in shell.json, and the wallpaper rotation script
      lives separately at ~/.local/bin/caelestia-wallpaper-rotate.sh.

Sources:
  ~/.config/caelestia/shell.json
  ~/.local/bin/caelestia-wallpaper-rotate.sh
```

### `raga status`
Shows daemon health and index state. No conversational output — structured,
scannable.

```
$ raga status

Daemon:        running (pid 4821)
Watched dirs:  4  (~/Documents, ~/Projects, ~/.config, ~/Pictures)
Files indexed: 4,201
Pending queue: 0
Last update:   12 seconds ago
```

### `raga reindex <path>`
Forces indexing of a directory not yet watched, or a full re-scan of an
existing one. Shows a progress indicator (file count as it processes).

```
$ raga reindex ~/Projects/new-thing

Indexing ~/Projects/new-thing...
[####------] 142/310 files
```

### `raga chat`
Launches the TUI (see Section 3).

### v1.1 — Action commands (shell integration)
Actions are triggered through natural language inside `ask`/`chat`, not
separate subcommands. Confirmation prompts appear inline:

```
$ raga ask "delete that pdf about federated learning notes"

RAGA> Found: ~/Documents/federated-learning-notes.pdf
      Delete this file (moves to trash)? [y/N]
```

If multiple candidates match, they're listed as a numbered choice instead of
a yes/no:

```
RAGA> Multiple matches found:
      1) ~/Documents/federated-learning-notes.pdf
      2) ~/Projects/capstone-federated-ids/notes.pdf
      Which one? [1/2/cancel]
```

## 3. TUI (`raga chat`) — Screen Layout

Built with Textual. Single full-screen view, three regions:

```
┌─────────────────────────────────────────────────────────────┐
│  RAGA — chat                          daemon: ● healthy      │  ← status bar
├───────────────────────────────────────┬───────────────────────┤
│                                         │  Sources               │
│  > where's my wallpaper script          │  ─────────────────    │
│                                         │  ~/.local/bin/         │
│  It's at ~/.local/bin/caelestia-       │  caelestia-wallpaper-  │
│  wallpaper-rotate.sh — rotates every    │  rotate.sh             │
│  7 minutes from ~/Pictures/Wallpapers,  │                        │
│  synced via caelestia scheme set.       │  [Enter to preview]    │
│                                         │                        │
│  > _                                    │                        │  ← chat pane
│                                         │                        │  (left, scrollable)
│                                         │                        │
├───────────────────────────────────────┴───────────────────────┤
│  [Enter] send   [Tab] focus sources   [Ctrl+C] quit             │  ← keybind footer
└─────────────────────────────────────────────────────────────┘
```

**Regions:**
- **Status bar (top):** daemon health, files indexed count — live-updating,
  matches `raga status` data.
- **Chat pane (left, primary):** scrollable conversation history, most recent
  at bottom, standard chat-input behavior.
- **Sources panel (right):** updates per-answer, lists cited files. Pressing
  Enter on a highlighted source shows a snippet preview inline (does not leave
  the TUI).
- **Footer:** keybind hints, always visible.

**Interaction model:**
- Keyboard-only navigation (Tab to move focus between chat input and sources
  panel, arrow keys to scroll history/select a source).
- No mouse requirement — fits a keyboard-first, terminal-native workflow.
- Follow-up questions retain conversation context within the session.

## 4. Design Principles

- **No unnecessary chrome.** The TUI shows exactly three regions — chat,
  sources, status — nothing decorative.
- **Sources are never hidden.** Every answer must have a visible,
  navigable source list — this is core to trust in the tool (see NFR-4 /
  privacy positioning), not an optional detail.
- **Destructive actions always interrupt the flow** with an explicit
  confirmation — never a passive inline warning that's easy to miss.
- **CLI output stays scriptable.** `ask`, `status`, and `reindex` output
  should remain clean enough to pipe/parse (e.g., `raga status --json` as a
  future flag), since scripting is a core use case for a CLI-first tool.

## 5. Out of Scope for This Spec

- Web UI wireframes — not part of v1/v1.1 (see Requirements, deferred to a
  possible future FastAPI-backed phase).
- Walker/Vicinae launcher UI — deferred; when built, it will reuse the same
  Core Engine `ask` output, not a new design.
