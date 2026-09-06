"""
RAGA TUI — Modern, responsive terminal UI for local document intelligence.

Layout:
  ┌── Header: ◈ RAGA · Local Intelligence ────────── ● daemon healthy · N files ──┐
  │ ╭─ Chat Stream (62%) ───────────────╮ ╭─ Sources & Preview (38%) ────────────╮│
  │ │                                   │ │ SOURCES (5)                          ││
  │ │  [User Query]                     │ │  1. [PDF]  paper.pdf                 ││
  │ │  [RAGA Response + Badge]          │ │     /CAPSTONE/                       ││
  │ │                                   │ │ ──────────────────────────────────── ││
  │ │                                   │ │ PREVIEW                              ││
  │ │                                   │ │ [Chunk content snippet...]           ││
  │ ╰───────────────────────────────────╯ ╰──────────────────────────────────────╯│
  │ ╭─ Prompt Input ────────────────────────────────────────────────────────────╮│
  │ │ > Ask anything...                                                         ││
  │ ╰───────────────────────────────────────────────────────────────────────────╯│
  └── Footer: [Enter] Send  [Tab] Sources  [1-5] Preview  [^Y] Copy  [^C] Quit ───┘
"""
from __future__ import annotations

import time
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on, work
from textual.widgets import Footer, Input, Label, ListItem, ListView, Static

from rich.text import Text


# ─── File Type Badges & Colors ────────────────────────────────────────────────

_TYPE_TAGS: dict[str, tuple[str, str]] = {
    ".pdf":  ("PDF",  "#ff7b72"),
    ".docx": ("DOCX", "#79c0ff"), ".pptx": ("PPTX", "#79c0ff"),
    ".xlsx": ("XLSX", "#7ee787"), ".odt":  ("ODT",  "#79c0ff"),
    ".odp":  ("ODP",  "#79c0ff"), ".ods":  ("ODS",  "#7ee787"),
    ".py":   ("PY",   "#f0883e"), ".js":   ("JS",   "#f0883e"),
    ".ts":   ("TS",   "#f0883e"), ".jsx":  ("JSX",  "#f0883e"),
    ".tsx":  ("TSX",  "#f0883e"), ".sh":   ("SH",   "#f0883e"),
    ".md":   ("MD",   "#d2a8ff"), ".txt":  ("TXT",  "#c9d1d9"),
    ".json": ("JSON", "#f0883e"), ".csv":  ("CSV",  "#7ee787"),
    ".jpg":  ("IMG",  "#d2a8ff"), ".png":  ("IMG",  "#d2a8ff"),
    ".jpeg": ("IMG",  "#d2a8ff"), ".webp": ("IMG",  "#d2a8ff"),
    ".mp3":  ("AUD",  "#39d353"), ".mp4":  ("VID",  "#39d353"),
    ".mkv":  ("VID",  "#39d353"), ".zip":  ("ZIP",  "#8b949e"),
}
_DEFAULT_TAG = ("FILE", "#8b949e")

_BADGE_CLR = {
    "filesystem": ("FILESYSTEM", "#7ee787"),
    "location":   ("LOCATION",   "#79c0ff"),
    "content":    ("CONTENT",    "#f0883e"),
}


def _type_tag(path: str) -> tuple[str, str]:
    return _TYPE_TAGS.get(Path(path).suffix.lower(), _DEFAULT_TAG)


def _relative_folder(path: str) -> str:
    """Return a clean parent folder relative to Documents/NMIMS or home."""
    parts = Path(path).parts
    try:
        idx = next(i for i, p in enumerate(parts) if p.lower() == "nmims")
        rel = "/".join(parts[idx + 1 : -1])
        return f"NMIMS/{rel}" if rel else "NMIMS"
    except StopIteration:
        try:
            return str(Path(path).parent.relative_to(Path.home()))
        except Exception:
            return str(Path(path).parent)[-35:]


def _daemon_status() -> str:
    try:
        from storage import metadata_db
        import sqlite3
        conn = metadata_db.get_connection()
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT COUNT(*) as n FROM files WHERE status='indexed'"
        ).fetchone()
        return f"● daemon healthy · {row['n']:,} files indexed"
    except Exception:
        return "○ daemon offline"


# ─── Rich Text Builders (No markup parsing bugs) ──────────────────────────────

def _make_hero_banner() -> Text:
    t = Text()
    t.append("\n")
    t.append("   ██████╗  █████╗  ██████╗  █████╗ \n", style="bold #58a6ff")
    t.append("   ██╔══██╗██╔══██╗██╔════╝ ██╔══██╗\n", style="bold #58a6ff")
    t.append("   ██████╔╝███████║██║  ███╗███████║\n", style="bold #79c0ff")
    t.append("   ██╔══██╗██╔══██║██║   ██║██╔══██║\n", style="bold #79c0ff")
    t.append("   ██║  ██║██║  ██║╚██████╔╝██║  ██║\n", style="bold #7ee787")
    t.append("   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝\n", style="bold #7ee787")
    t.append("   local file intelligence & semantic search\n\n", style="italic #8b949e")
    t.append("   Try asking:\n", style="bold #c9d1d9")
    t.append("   • ", style="#58a6ff")
    t.append('"who are the authors of the fltrust paper"\n', style="#8b949e")
    t.append("   • ", style="#58a6ff")
    t.append('"where are my capstone notes"\n', style="#8b949e")
    t.append("   • ", style="#58a6ff")
    t.append('"list folders in nmims"\n', style="#8b949e")
    t.append("   • ", style="#58a6ff")
    t.append('"what was in CN experiment 5"\n\n', style="#8b949e")
    return t


def _make_user_msg(query: str) -> Text:
    t = Text()
    t.append("\n❯ ", style="bold #58a6ff")
    t.append(query + "\n", style="bold #ffffff")
    return t


def _make_raga_msg(qtype: str, body: str) -> Text:
    t = Text()
    t.append("◈ RAGA", style="bold #58a6ff")
    if qtype in _BADGE_CLR:
        badge_name, badge_color = _BADGE_CLR[qtype]
        t.append(f"  [{badge_name}]", style=f"bold {badge_color}")
    t.append("\n\n")
    t.append(body)
    return t


def _make_preview_msg(filename: str, folder: str, snippet: str) -> Text:
    t = Text()
    t.append(f"📄 {filename}\n", style="bold #ffffff")
    t.append(f"📁 {folder}\n", style="#8b949e")
    t.append("─" * 36 + "\n", style="#21262d")
    t.append(snippet, style="#c9d1d9")
    return t


# ─── Widgets ──────────────────────────────────────────────────────────────────

class SourceEntry(ListItem):
    """A single interactive source entry in the sidebar."""

    def __init__(self, n: int, path: str, chunk_text: str) -> None:
        super().__init__()
        self.source_path = path
        self.chunk_text = chunk_text
        self._n = n

    def compose(self) -> ComposeResult:
        label, color = _type_tag(self.source_path)
        name = Path(self.source_path).name
        folder = _relative_folder(self.source_path)
        t = Text()
        t.append(f" {self._n}. ", style="bold #8b949e")
        t.append(f"[{label}]", style=f"bold {color}")
        t.append(f" {name}\n", style="bold #ffffff")
        t.append(f"    {folder}/", style="#8b949e")
        yield Static(t)


# ─── App ──────────────────────────────────────────────────────────────────────

class RagaApp(App):
    """RAGA — Modern Local Document Intelligence TUI."""

    TITLE = "raga"

    CSS = """
    Screen {
        background: #0b0e14;
        color: #c9d1d9;
    }

    /* ── Header ── */
    #header-bar {
        height: 3;
        background: #11151c;
        border-bottom: solid #21262d;
        layout: horizontal;
        padding: 0 1;
    }
    #header-title {
        width: auto;
        color: #58a6ff;
        text-style: bold;
        content-align: left middle;
    }
    #header-subtitle {
        width: auto;
        color: #8b949e;
        padding-left: 1;
        content-align: left middle;
    }
    #header-status {
        width: 1fr;
        color: #7ee787;
        content-align: right middle;
        text-align: right;
    }

    /* ── Main Layout ── */
    #main-container {
        height: 1fr;
        padding: 0;
    }

    /* ── Chat Stream (Left) ── */
    #chat-scroll {
        width: 62%;
        background: #0b0e14;
        border-right: solid #21262d;
        padding: 1 2;
    }

    /* ── Sources & Preview Panel (Right) ── */
    #sidebar {
        width: 38%;
        background: #0e121a;
        padding: 1 1;
        layout: vertical;
    }
    #sources-header {
        color: #58a6ff;
        text-style: bold;
        height: 1;
        margin-bottom: 1;
        padding-left: 1;
    }
    #sources-list {
        height: 48%;
        background: #11151c;
        border: solid #21262d;
        scrollbar-size: 1 1;
    }
    #sources-list > ListItem {
        padding: 0 1;
        height: auto;
        border-bottom: solid #161b22;
    }
    #sources-list > ListItem:hover {
        background: #161f2e;
    }
    #sources-list > ListItem.--highlight {
        background: #1a2333;
        border-left: solid #58a6ff;
    }

    #preview-header {
        color: #8b949e;
        text-style: bold;
        height: 1;
        margin-top: 1;
        margin-bottom: 0;
        padding-left: 1;
    }
    #preview-area {
        height: 1fr;
        background: #11151c;
        border: solid #21262d;
        padding: 1 1;
        overflow-y: auto;
        scrollbar-size: 1 1;
    }

    /* ── Input Box ── */
    #input-container {
        height: 3;
        background: #11151c;
        border-top: solid #21262d;
        padding: 0 1;
    }
    #query-input {
        width: 100%;
        height: 3;
        background: #11151c;
        border: none;
        color: #ffffff;
        padding: 0 1;
    }
    #query-input:focus {
        border: none;
    }

    /* ── Footer ── */
    Footer {
        background: #0e121a;
        color: #8b949e;
        border-top: solid #161b22;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("tab", "focus_sources", "Sources"),
        Binding("ctrl+backslash", "toggle_sources", "Toggle Sidebar"),
        Binding("ctrl+y", "copy_answer", "Copy Answer"),
        Binding("1", "quick_preview('1')", "1", show=False),
        Binding("2", "quick_preview('2')", "2", show=False),
        Binding("3", "quick_preview('3')", "3", show=False),
        Binding("4", "quick_preview('4')", "4", show=False),
        Binding("5", "quick_preview('5')", "5", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._live_msg: Static | None = None
        self._last_answer: str = ""
        self._chunks: list[dict] = []
        self._history: list[dict] = []

    def compose(self) -> ComposeResult:
        # ── Header ──
        with Horizontal(id="header-bar"):
            yield Static("◈ RAGA", id="header-title")
            yield Static("· local file intelligence", id="header-subtitle")
            yield Static(_daemon_status(), id="header-status")

        # ── Body ──
        with Horizontal(id="main-container"):
            # Left: Chat stream
            with VerticalScroll(id="chat-scroll"):
                yield Static(_make_hero_banner())

            # Right: Sources & Preview Sidebar
            with Vertical(id="sidebar"):
                yield Label("SOURCES (0)", id="sources-header")
                yield ListView(id="sources-list")
                yield Label("PREVIEW (select a source)", id="preview-header")
                with VerticalScroll(id="preview-area"):
                    yield Static(Text("No source selected. Run a query or press 1-5 to inspect.", style="#8b949e"), id="preview-text")

        # ── Bottom Input ──
        with Container(id="input-container"):
            yield Input(placeholder="Ask anything about your files... (or type 'where', 'list')", id="query-input")

        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#query-input", Input).focus()

    # ── Query Submission ───────────────────────────────────────────────────────

    @on(Input.Submitted, "#query-input")
    def handle_query(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return
        event.input.value = ""

        scroll = self.query_one("#chat-scroll", VerticalScroll)
        scroll.mount(Static(_make_user_msg(query)))
        scroll.scroll_end(animate=False)

        # Reset Sidebar
        self.query_one("#sources-list", ListView).clear()
        self.query_one("#sources-header", Label).update("SOURCES (...)")
        self.query_one("#preview-text", Static).update(Text("Loading sources...", style="#8b949e"))

        # Create streaming response container
        live = Static(_make_raga_msg("", "Searching index & files..."))
        self._live_msg = live
        scroll.mount(live)
        scroll.scroll_end(animate=False)

        self._do_ask(query)

    @work(thread=True)
    def _do_ask(self, query: str) -> None:
        from core.query_classifier import classify_query
        qtype = classify_query(query)

        # ── Filesystem / Location: Fast direct path, no LLM needed ──
        if qtype in ("filesystem", "location"):
            from core.engine import ask
            result = ask(query)
            text_body = result.get("text", "")
            self._last_answer = text_body
            self._history.append({"role": "user", "content": query})
            self._history.append({"role": "assistant", "content": text_body})
            self._history = self._history[-8:]
            self.call_from_thread(
                self._set_live,
                _make_raga_msg(qtype, text_body),
            )
            self.call_from_thread(
                self._finalize, result.get("sources", []), []
            )
            return

        # ── Multi-turn Context Resolution for Content Queries ──
        retrieval_query = query
        pronouns = {"they", "their", "them", "he", "she", "it", "its", "that", "this", "these", "those", "there", "who", "which"}
        query_words_lower = set(query.lower().split())
        if self._history and (len(query.split()) <= 4 or bool(query_words_lower & pronouns)):
            last_user_query = next((m["content"] for m in reversed(self._history) if m["role"] == "user"), "")
            if last_user_query:
                retrieval_query = f"{last_user_query} {query}"

        # ── Content: Hybrid retrieve → stream tokens ──
        from core.retriever import retrieve
        chunks = retrieve(retrieval_query, top_k=7)
        self._chunks = chunks

        if not chunks:
            self._last_answer = "Nothing relevant found in your indexed files."
            self.call_from_thread(
                self._set_live,
                _make_raga_msg(qtype, "Nothing relevant found in your indexed files."),
            )
            self.call_from_thread(self._finalize, [], chunks)
            return

        self.call_from_thread(
            self._set_live,
            _make_raga_msg(qtype, f"Found {len(chunks)} relevant chunks. Synthesizing answer..."),
        )

        from core.generator import generate_answer_streaming
        buffer = ""
        last_push = time.time()

        for token in generate_answer_streaming(query, chunks, history=self._history):
            buffer += token
            now = time.time()
            if now - last_push >= 0.04:
                snapshot = buffer
                self.call_from_thread(
                    self._set_live,
                    _make_raga_msg(qtype, snapshot),
                )
                last_push = now

        # Final render & record conversation turn
        self._last_answer = buffer
        self._history.append({"role": "user", "content": query})
        self._history.append({"role": "assistant", "content": buffer})
        self._history = self._history[-8:]

        self.call_from_thread(
            self._set_live,
            _make_raga_msg(qtype, buffer),
        )

        seen: set[str] = set()
        sources: list[str] = []
        for c in chunks:
            if c["file_path"] not in seen:
                seen.add(c["file_path"])
                sources.append(c["file_path"])

        self.call_from_thread(self._finalize, sources, chunks)

    # ── Thread-Safe Helpers ───────────────────────────────────────────────────

    def _set_live(self, content: Text) -> None:
        if self._live_msg is not None:
            self._live_msg.update(content)
            self.query_one("#chat-scroll", VerticalScroll).scroll_end(animate=False)

    def _finalize(self, sources: list[str], chunks: list[dict]) -> None:
        if self._live_msg is not None:
            scroll = self.query_one("#chat-scroll", VerticalScroll)
            t_sep = Text()
            t_sep.append("\n" + "─" * 60 + "\n", style="#21262d")
            scroll.mount(Static(t_sep))
            scroll.scroll_end(animate=False)
            self._live_msg = None

        # Populate sidebar sources
        src_list = self.query_one("#sources-list", ListView)
        src_list.clear()
        self.query_one("#sources-header", Label).update(f"SOURCES ({len(sources[:5])})")

        for i, path in enumerate(sources[:5], 1):
            chunk_text = next(
                (c["chunk_text"] for c in chunks if c["file_path"] == path),
                f"File: {path}"
            )
            src_list.append(SourceEntry(i, path, chunk_text))

        if not sources:
            src_list.append(ListItem(Static(Text("  No sources referenced", style="#8b949e"))))
            self.query_one("#preview-text", Static).update(Text("No sources found for this query.", style="#8b949e"))
        elif sources:
            # Auto-preview the #1 source
            first_path = sources[0]
            first_chunk = next(
                (c["chunk_text"] for c in chunks if c["file_path"] == first_path),
                f"File: {first_path}"
            )
            self._render_preview(first_path, first_chunk)

        self.query_one("#query-input", Input).focus()

    def _render_preview(self, path: str, chunk_text: str) -> None:
        snippet = chunk_text[:800] + ("…" if len(chunk_text) > 800 else "")
        self.query_one("#preview-text", Static).update(
            _make_preview_msg(Path(path).name, _relative_folder(path), snippet)
        )

    # ── Source Selection & Preview ────────────────────────────────────────────

    @on(ListView.Selected, "#sources-list")
    def on_source_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, SourceEntry):
            self._render_preview(item.source_path, item.chunk_text)

    # ── Keybindings ───────────────────────────────────────────────────────────

    def action_focus_sources(self) -> None:
        self.query_one("#sources-list", ListView).focus()

    def action_toggle_sources(self) -> None:
        sidebar = self.query_one("#sidebar", Vertical)
        chat = self.query_one("#chat-scroll", VerticalScroll)
        sidebar.display = not sidebar.display
        chat.styles.width = "100%" if not sidebar.display else "62%"

    def action_copy_answer(self) -> None:
        if not self._last_answer:
            return
        try:
            import subprocess
            res = subprocess.run(["wl-copy"], input=self._last_answer.encode(), capture_output=True)
            if res.returncode != 0:
                subprocess.run(["xclip", "-selection", "clipboard"], input=self._last_answer.encode(), capture_output=True)
            self.notify("Answer copied to clipboard!", timeout=2)
        except Exception:
            self.notify("Clipboard tool not found (install wl-clipboard or xclip)", timeout=3)

    def action_quick_preview(self, n: str) -> None:
        src_list = self.query_one("#sources-list", ListView)
        idx = int(n) - 1
        entries = list(src_list.query(SourceEntry))
        if 0 <= idx < len(entries):
            entries[idx].scroll_visible()
            src_list.index = idx
            self._render_preview(entries[idx].source_path, entries[idx].chunk_text)
