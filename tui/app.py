"""
OpenCode-spec Terminal User Interface (TUI) for RAGA.

Visual Design:
  - Nord dark theme by default (#2E3440, #3B4252, #434C5E, #88C0D0, #ECEFF4)
  - Multi-theme registry (nord, opencode, tokyonight, catppuccin, gruvbox, one-dark, matrix)
  - Config persistence in ~/.config/raga/tui.json

Layout:
  - Top Session Bar / Tabs: Active Session #1, Model Info, Live Status Indicator
  - Split-Footer Architecture:
      - Left: Scrollback Transcript with UserCards, Collapsible Thinking Blocks, Markdown Stream, [📋 Copy]
      - Right: Active Context Sources Sidebar (Confidence Meters, Type Badges, Chunk Preview)
      - Bottom: Autocomplete Popup (/ for commands, @ for files), Input Box, Bottom Statusbar
  - Command Palette Modal (Ctrl+P) for searchable actions
"""
from __future__ import annotations

import inspect
import time
import sqlite3
from pathlib import Path
from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.css.stylesheet import Stylesheet
from textual.screen import ModalScreen
from textual import on, work, events
from textual.widgets import Footer, Input, Label, ListItem, ListView, Static, OptionList

from rich.text import Text
from rich.markdown import Markdown

from tui.theme import Theme, get_theme, THEMES, load_config, save_config, generate_css

# ─── Braille Spinner Frames ───────────────────────────────────────────────────

_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# ─── File Type Badges & Icons ─────────────────────────────────────────────────

_TYPE_TAGS: dict[str, tuple[str, str, str]] = {
    ".pdf":  ("PDF",  "#ff7b72", "📄"),
    ".docx": ("DOCX", "#79c0ff", "📝"), ".doc":  ("DOC",  "#79c0ff", "📝"),
    ".pptx": ("PPTX", "#f0883e", "📊"), ".ppt":  ("PPT",  "#f0883e", "📊"),
    ".xlsx": ("XLSX", "#7ee787", "📈"), ".xls":  ("XLS",  "#7ee787", "📈"),
    ".odt":  ("ODT",  "#79c0ff", "📝"), ".odp":  ("ODP",  "#f0883e", "📊"),
    ".ods":  ("ODS",  "#7ee787", "📈"),
    ".py":   ("PY",   "#38bdf8", "⚡"), ".js":   ("JS",   "#f1e05a", "⚡"),
    ".ts":   ("TS",   "#3178c6", "⚡"), ".jsx":  ("JSX",  "#58a6ff", "⚡"),
    ".tsx":  ("TSX",  "#58a6ff", "⚡"), ".sh":   ("SH",   "#7ee787", "⚡"),
    ".rs":   ("RUST", "#f0883e", "⚡"), ".go":   ("GO",   "#79c0ff", "⚡"),
    ".c":    ("C",    "#79c0ff", "⚡"), ".cpp":  ("C++",  "#79c0ff", "⚡"),
    ".java": ("JAVA", "#ff7b72", "⚡"),
    ".md":   ("MD",   "#d2a8ff", "📜"), ".txt":  ("TXT",  "#c9d1d9", "📄"),
    ".json": ("JSON", "#e3b341", "⚙️"), ".yaml": ("YAML", "#f0883e", "⚙️"),
    ".yml":  ("YML",  "#f0883e", "⚙️"), ".toml": ("TOML", "#f0883e", "⚙️"),
    ".csv":  ("CSV",  "#7ee787", "📊"),
    ".jpg":  ("IMG",  "#d2a8ff", "🖼️"), ".png":  ("IMG",  "#d2a8ff", "🖼️"),
    ".jpeg": ("IMG",  "#d2a8ff", "🖼️"), ".webp": ("IMG",  "#d2a8ff", "🖼️"),
    ".mp3":  ("AUD",  "#34d399", "🎵"), ".mp4":  ("VID",  "#34d399", "🎬"),
    ".mkv":  ("VID",  "#34d399", "🎬"), ".zip":  ("ZIP",  "#8b949e", "📦"),
    ".tar":  ("TAR",  "#8b949e", "📦"), ".gz":   ("GZ",   "#8b949e", "📦"),
}
_DEFAULT_TAG = ("FILE", "#8b949e", "📁")


def _type_tag(path: str) -> tuple[str, str, str]:
    name_lower = Path(path).name.lower()
    if name_lower in ("dockerfile", "dockerfile-alpine", "containerfile"):
        return ("DOCKER", "#38bdf8", "🐳")
    if name_lower in ("makefile", "gnumakefile"):
        return ("MAKE", "#f0883e", "⚙️")
    return _TYPE_TAGS.get(Path(path).suffix.lower(), _DEFAULT_TAG)


def _relative_folder(path: str) -> str:
    """Return a clean directory breadcrumb relative to NMIMS or home."""
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


def _daemon_file_count() -> int:
    try:
        from storage import metadata_db
        conn = metadata_db.get_connection()
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT COUNT(*) as n FROM files WHERE status='indexed'").fetchone()
        return row["n"] if row else 0
    except Exception:
        return 0


# ─── Clickable Copy Button Widget ─────────────────────────────────────────────

class CopyButton(Static):
    """A sleek clickable Copy button for top-right of AI response cards."""

    DEFAULT_CSS = """
    CopyButton {
        width: auto;
        height: 1;
        padding: 0 1;
        background: #434C5E;
        color: #88C0D0;
        text-style: bold;
        border: none;
    }
    CopyButton:hover {
        background: #88C0D0;
        color: #2E3440;
    }
    """

    def __init__(self, text: str = "") -> None:
        super().__init__("📋 Copy")
        self.text_to_copy = text

    def on_click(self) -> None:
        if not self.text_to_copy:
            return
        try:
            import subprocess
            res = subprocess.run(["wl-copy"], input=self.text_to_copy.encode(), capture_output=True)
            if res.returncode != 0:
                subprocess.run(["xclip", "-selection", "clipboard"], input=self.text_to_copy.encode(), capture_output=True)
            self.update("✔ Copied!")
            self.styles.color = "#A3BE8C"
            self.styles.background = "#3B4252"
            self.set_timer(2.0, self._reset_text)
            self.app.notify("Answer copied to clipboard!", timeout=2)
        except Exception:
            self.app.notify("Clipboard utility (wl-copy/xclip) not available", timeout=3)

    def _reset_text(self) -> None:
        self.update("📋 Copy")
        self.styles.color = "#88C0D0"
        self.styles.background = "#434C5E"


# ─── Rich Visual Builders ─────────────────────────────────────────────────────

def _make_hero_banner(file_count: int, theme: Theme) -> Text:
    t = Text()
    t.append("\n")
    t.append("   ██████╗  █████╗  ██████╗  █████╗ \n", style=f"bold {theme.primary}")
    t.append("   ██╔══██╗██╔══██╗██╔════╝ ██╔══██╗\n", style=f"bold {theme.primary}")
    t.append("   ██████╔╝███████║██║  ███╗███████║\n", style=f"bold {theme.secondary}")
    t.append("   ██╔══██╗██╔══██║██║   ██║██╔══██║\n", style=f"bold {theme.secondary}")
    t.append("   ██║  ██║██║  ██║╚██████╔╝██║  ██║\n", style=f"bold {theme.success}")
    t.append("   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝\n", style=f"bold {theme.success}")
    t.append("   LOCAL INTELLIGENCE & SEMANTIC KNOWLEDGE BASE\n", style=f"bold {theme.text_subtle}")
    t.append(f"   ⚡ Qwen 2.5 3B · GPU   📁 {file_count:,} files indexed   🔍 Hybrid RAG + CrossEncoder\n\n", style=theme.text_muted)
    t.append("   💡 Example queries / commands:\n", style=f"bold {theme.text}")
    t.append(f"   ┌─ Quick Starters ({theme.name} theme) ──────────────────────────────────────────────┐\n", style=theme.border)
    t.append("   │ ", style=theme.border)
    t.append("❯ who are the authors of the fltrust   ", style=theme.primary)
    t.append("│ ", style=theme.border)
    t.append("❯ which of my projects use docker      ", style=theme.primary)
    t.append("│\n", style=theme.border)
    t.append("   │ ", style=theme.border)
    t.append("❯ list all the CC sem vii resources    ", style=theme.primary)
    t.append("│ ", style=theme.border)
    t.append("❯ explain the working of codelens      ", style=theme.primary)
    t.append("│\n", style=theme.border)
    t.append("   │ ", style=theme.border)
    t.append("❯ /themes to switch colors             ", style=theme.accent)
    t.append("│ ", style=theme.border)
    t.append("❯ Ctrl+P for Command Palette           ", style=theme.accent)
    t.append("│\n", style=theme.border)
    t.append(f"   └─────────────────────────────────────────────────────────────────────────────┘\n\n", style=theme.border)
    return t


def _make_user_msg(query: str, theme: Theme) -> Text:
    t = Text()
    timestamp = datetime.now().strftime("%H:%M")
    t.append(" ❯ ", style=f"bold {theme.primary}")
    t.append("YOU  ", style=f"bold {theme.primary}")
    t.append(f"{timestamp}\n\n", style=theme.text_subtle)
    t.append(f" {query}\n", style=f"bold {theme.text}")
    return t


def _make_raga_header(qtype: str, theme: Theme) -> Text:
    t = Text()
    timestamp = datetime.now().strftime("%H:%M")
    t.append(" ◈ ", style=f"bold {theme.tertiary}")
    t.append("RAGA  ", style=f"bold {theme.tertiary}")
    badge_map = {
        "filesystem": ("FILESYSTEM", theme.success, f"on {theme.bg_surface}"),
        "location":   ("LOCATION",   theme.primary, f"on {theme.bg_surface}"),
        "content":    ("CONTENT",    theme.warning, f"on {theme.bg_surface}"),
        "system":     ("SYSTEM",     theme.tertiary, f"on {theme.bg_surface}"),
    }
    if qtype in badge_map:
        badge_name, fg, bg = badge_map[qtype]
        t.append(f" {badge_name} ", style=f"bold {fg} {bg}")
    t.append(f"  {timestamp}", style=theme.text_subtle)
    return t


def _make_preview_msg(path: str, snippet: str, theme: Theme) -> Text:
    label, color, icon = _type_tag(path)
    name = Path(path).name
    folder = _relative_folder(path)
    t = Text()
    t.append(f"{icon} {name}\n", style=f"bold {theme.text}")
    t.append(f"📁 {folder}/\n", style=theme.text_subtle)
    t.append("─" * 40 + "\n", style=theme.border)
    t.append(snippet, style=theme.text_muted)
    return t


# ─── Custom Message Card Widgets ──────────────────────────────────────────────

class UserCard(Container):
    """An elevated card container for user prompts."""
    def __init__(self, query: str, theme: Theme) -> None:
        super().__init__()
        self.query_text = query
        self.theme = theme

    def compose(self) -> ComposeResult:
        yield Static(_make_user_msg(self.query_text, self.theme))


class RagaCard(Container):
    """An elevated card container for assistant answers with top-right copy button."""
    def __init__(self, theme: Theme) -> None:
        super().__init__()
        self.theme = theme
        self.copy_btn = CopyButton("")
        self.title_widget = Static(_make_raga_header("content", theme), classes="card-title")
        self.thinking_widget = Static("", classes="thinking-box")
        self.thinking_widget.display = False
        self.body_widget = Static(Markdown("⠋ *Searching index & reranking candidate files...*"), classes="card-body")
        self.stats_widget = Static("", classes="card-stats")

    def compose(self) -> ComposeResult:
        with Horizontal(classes="card-header-row"):
            yield self.title_widget
            yield self.copy_btn
        yield self.thinking_widget
        yield self.body_widget
        yield self.stats_widget


class SystemCard(Container):
    """An elevated card container for system notifications & slash commands."""

    def __init__(self, markdown_text: str, theme: Theme) -> None:
        super().__init__()
        self.markdown_text = markdown_text
        self.theme = theme

    def compose(self) -> ComposeResult:
        with Horizontal(classes="card-header-row"):
            yield Static(_make_raga_header("system", self.theme), classes="card-title")
        yield Static(Markdown(self.markdown_text), classes="card-body")


class SourceEntry(ListItem):
    """An interactive source entry with file type tag and visual relevance meter."""

    def __init__(self, n: int, path: str, chunk_text: str, score: float = 0.0, theme: Theme | None = None) -> None:
        super().__init__()
        self.source_path = path
        self.chunk_text = chunk_text
        self._n = n
        self._score = score
        self.theme = theme or get_theme()

    def compose(self) -> ComposeResult:
        label, color, icon = _type_tag(self.source_path)
        name = Path(self.source_path).name
        folder = _relative_folder(self.source_path)

        pct = int(round(self._score * 100)) if self._score > 0 else 0
        filled = int(round(self._score * 6)) if self._score > 0 else 0
        bar = "█" * filled + "░" * (6 - filled)

        t = Text()
        t.append(f" {self._n}. ", style=f"bold {self.theme.text_subtle}")
        t.append(f"[{label}]", style=f"bold {color}")
        t.append(f" {name}", style=f"bold {self.theme.text}")
        if self._score > 0:
            meter_style = self.theme.primary if pct >= 80 else (self.theme.success if pct >= 50 else self.theme.warning if pct >= 25 else self.theme.text_subtle)
            t.append(f"  {bar} {pct}%\n", style=f"bold {meter_style}")
        else:
            t.append("\n")
        t.append(f"    {folder}/", style=self.theme.text_subtle)
        yield Static(t)


# ─── Command Palette Modal Screen ─────────────────────────────────────────────

class CommandPaletteModal(ModalScreen[str]):
    """Searchable command palette modal (Ctrl+P)."""

    ACTIONS = [
        ("🎨 Switch Theme: Nord", "theme:nord"),
        ("🎨 Switch Theme: OpenCode", "theme:opencode"),
        ("🎨 Switch Theme: Tokyo Night", "theme:tokyonight"),
        ("🎨 Switch Theme: Catppuccin", "theme:catppuccin"),
        ("🎨 Switch Theme: Gruvbox", "theme:gruvbox"),
        ("🎨 Switch Theme: One Dark", "theme:one-dark"),
        ("🎨 Switch Theme: Matrix", "theme:matrix"),
        ("🔄 Reindex All Files", "cmd:reindex"),
        ("🧹 Clear Chat History", "cmd:clear"),
        ("📊 System Status & Telemetry", "cmd:status"),
        ("📋 Copy Last Answer", "cmd:copy"),
        ("📦 Toggle Sources Sidebar", "cmd:toggle_sidebar"),
        ("❓ Show Help & Keybindings", "cmd:help"),
        ("🚪 Exit RAGA", "cmd:exit"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="palette-modal"):
            with Container(id="palette-dialog"):
                yield Label("⚡ Command Palette (type to filter, Enter to run)", id="palette-title")
                yield Input(placeholder="Search actions or switch themes...", id="palette-input")
                yield ListView(id="palette-list")

    def on_mount(self) -> None:
        self.query_one("#palette-input", Input).focus()
        self._populate_list("")

    def _populate_list(self, filter_text: str) -> None:
        lv = self.query_one("#palette-list", ListView)
        lv.clear()
        query = filter_text.strip().lower()
        for label, val in self.ACTIONS:
            if not query or query in label.lower() or query in val.lower():
                lv.append(ListItem(Static(label), id=f"item_{val.replace(':', '_').replace('-', '_')}"))

    @on(Input.Changed, "#palette-input")
    def on_filter_changed(self, event: Input.Changed) -> None:
        self._populate_list(event.value)

    @on(ListView.Selected, "#palette-list")
    def on_item_selected(self, event: ListView.Selected) -> None:
        if event.item and event.item.id:
            raw_val = event.item.id.replace("item_", "", 1).replace("_", ":", 1)
            self.dismiss(raw_val)

    def key_escape(self) -> None:
        self.dismiss("")


# ─── Main Application ─────────────────────────────────────────────────────────

class RagaApp(App):
    """RAGA — Modern OpenCode-spec TUI for Local Document Intelligence."""

    TITLE = "raga"

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+p", "command_palette", "Palette"),
        Binding("tab", "focus_sources", "Sources"),
        Binding("ctrl+backslash", "toggle_sources", "Toggle Sidebar"),
        Binding("ctrl+y", "copy_answer", "Copy Answer"),
        Binding("ctrl+l", "clear_chat", "Clear Screen"),
        Binding("1", "quick_preview('1')", "1", show=False),
        Binding("2", "quick_preview('2')", "2", show=False),
        Binding("3", "quick_preview('3')", "3", show=False),
        Binding("4", "quick_preview('4')", "4", show=False),
        Binding("5", "quick_preview('5')", "5", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config = load_config()
        self.active_theme = get_theme(self.config.get("theme", "nord"))
        self.CSS = generate_css(self.active_theme)
        self._active_card: RagaCard | None = None
        self._last_answer: str = ""
        self._chunks: list[dict] = []
        self._history: list[dict] = []
        self._file_count = _daemon_file_count()
        self._spinner_idx = 0

    def compose(self) -> ComposeResult:
        # ── Top Session Bar / Tabs ──
        with Horizontal(id="session-bar"):
            yield Static("◈  R A G A  [#1 Session]", classes="session-tab", id="session-title")
            yield Static("· 🧠 qwen2.5:3b (GPU)", classes="session-meta", id="session-meta")
            yield Static(f"● ONLINE · {self._file_count:,} files", classes="session-status", id="session-status")

        # ── Main 2-Pane Body ──
        with Horizontal(id="main-container"):
            # Left: Chat scrollback transcript
            with VerticalScroll(id="chat-scroll"):
                yield Static(_make_hero_banner(self._file_count, self.active_theme), id="hero-banner")

            # Right: Sources Sidebar & Preview
            with Vertical(id="sidebar"):
                yield Label("📦 SOURCES (0)", id="sources-header")
                yield ListView(id="sources-list")
                yield Label("📄 CHUNK PREVIEW", id="preview-header")
                with VerticalScroll(id="preview-area"):
                    yield Static(
                        Text("No source selected. Run a query or press 1-5 to inspect.", style=self.active_theme.text_subtle),
                        id="preview-text"
                    )

        # ── Split-Footer Vertical Stack ──
        with Vertical(id="footer-stack"):
            # Autocomplete popup
            with Container(id="autocomplete-popup"):
                yield OptionList(id="autocomplete-options")

            # Composer / Input box
            with Container(id="input-container"):
                yield Input(
                    placeholder="Ask anything about your files, code, or notes... (or type / for commands, @ for files)",
                    id="query-input"
                )

            # Bottom Statusbar line
            with Horizontal(id="statusbar"):
                yield Static("qwen2.5:3b · GPU", classes="statusbar-left")
                yield Static(f"📁 {self._file_count:,} files · 🎨 {self.active_theme.name}", classes="statusbar-mid", id="statusbar-mid")
                yield Static("^P Palette · ^X Leader · Tab Sources · ^C Quit", classes="statusbar-right")

    def on_mount(self) -> None:
        self.query_one("#query-input", Input).focus()
        self._warmup_models()

    @work(thread=True)
    def _warmup_models(self) -> None:
        """Pre-warm reranker and embeddings in background so first query has zero latency."""
        try:
            from core.reranker import warmup_reranker
            warmup_reranker()
        except Exception:
            pass

    # ── Autocomplete / Slash Command Detection ─────────────────────────────────

    @on(Input.Changed, "#query-input")
    def on_input_changed(self, event: Input.Changed) -> None:
        if not self.is_mounted:
            return
        try:
            popup = self.query_one("#autocomplete-popup", Container)
            ac_opts = self.query_one("#autocomplete-options", OptionList)
        except Exception:
            return

        val = event.value
        if val.startswith("/"):
            # Slash commands menu
            commands = [
                ("/themes", "🎨 Switch color theme (nord, tokyonight, catppuccin, matrix...)"),
                ("/models", "🧠 Display active LLM model info"),
                ("/status", "📊 View indexing telemetry & database health"),
                ("/reindex", "🔄 Trigger full background reindexing"),
                ("/clear", "🧹 Clear chat history and restart transcript"),
                ("/copy", "📋 Copy latest answer to system clipboard"),
                ("/help", "❓ Show all keybindings and command guide"),
                ("/exit", "🚪 Quit RAGA application"),
            ]
            matching = [c for c in commands if c[0].startswith(val.split()[0])]
            if matching:
                ac_opts.clear_options()
                for cmd, desc in matching:
                    t = Text()
                    t.append(f"{cmd:<10}", style=f"bold {self.active_theme.primary}")
                    t.append(f" {desc}", style=self.active_theme.text_muted)
                    ac_opts.add_option(t)
                popup.display = True
                return

        elif "@" in val:
            # File mention fuzzy matching
            at_idx = val.rfind("@")
            file_query = val[at_idx + 1:].strip().lower()
            try:
                from storage import metadata_db
                conn = metadata_db.get_connection()
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT path FROM files WHERE status='indexed' AND path LIKE ? LIMIT 6",
                    (f"%{file_query}%",)
                ).fetchall()
                if rows:
                    ac_opts.clear_options()
                    for r in rows:
                        p = r["path"]
                        name = Path(p).name
                        folder = _relative_folder(p)
                        t = Text()
                        t.append(f"@{name:<30}", style=f"bold {self.active_theme.primary}")
                        t.append(f" 📁 {folder}", style=self.active_theme.text_subtle)
                        ac_opts.add_option(t)
                    popup.display = True
                    return
            except Exception:
                pass

        popup.display = False

    @on(OptionList.OptionSelected, "#autocomplete-options")
    def on_autocomplete_selected(self, event: OptionList.OptionSelected) -> None:
        prompt_opt = event.option.prompt
        plain_text = prompt_opt.plain if isinstance(prompt_opt, Text) else str(prompt_opt)
        cmd_word = plain_text.split()[0]
        inp = self.query_one("#query-input", Input)
        if cmd_word.startswith("/"):
            inp.value = f"{cmd_word} "
        elif cmd_word.startswith("@"):
            cur_val = inp.value
            at_idx = cur_val.rfind("@")
            inp.value = cur_val[:at_idx] + cmd_word + " "
        self.query_one("#autocomplete-popup", Container).display = False
        inp.focus()

    # ── Query Submission & Slash Command Dispatch ──────────────────────────────

    @on(Input.Submitted, "#query-input")
    def handle_query(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return
        event.input.value = ""
        self.query_one("#autocomplete-popup", Container).display = False

        # Check for Slash Commands
        if query.startswith("/"):
            self._handle_slash_command(query)
            return

        scroll = self.query_one("#chat-scroll", VerticalScroll)

        # 1. Mount User Message Card
        user_card = UserCard(query, self.active_theme)
        scroll.mount(user_card)

        # Reset Sidebar
        self.query_one("#sources-list", ListView).clear()
        self.query_one("#sources-header", Label).update("📦 SOURCES (...)")
        self.query_one("#preview-text", Static).update(Text("Searching & indexing...", style=self.active_theme.text_subtle))

        # 2. Mount Assistant Response Card
        raga_card = RagaCard(self.active_theme)
        scroll.mount(raga_card)
        scroll.scroll_end(animate=False)

        self._active_card = raga_card
        self._do_ask(query)

    def _handle_slash_command(self, cmd: str) -> None:
        parts = cmd.split()
        root = parts[0].lower()

        if root in ("/themes", "/theme", "/them"):
            if len(parts) > 1:
                target_theme = parts[1].lower()
                self._switch_theme(target_theme)
            else:
                available = ", ".join(THEMES.keys())
                self._mount_system_msg(f"**Available themes:** `{available}`\n\nUsage: `/themes nord`, `/themes tokyonight`, `/themes catppuccin`, etc.")
        elif root in ("/clear", "/new"):
            self.action_clear_chat()
        elif root == "/models":
            self._mount_system_msg("**Active LLM Engine:** `qwen2.5:3b` (Ollama, GPU Accelerated)\n**Embeddings:** `nomic-embed-text` · **Reranker:** `ms-marco-MiniLM-L-6-v2`")
        elif root == "/status":
            from core.status_engine import get_status
            s = get_status()
            self._mount_system_msg(
                f"### System Telemetry & Health\n"
                f"- **Daemon Status:** `Healthy`\n"
                f"- **Files Indexed:** `{s.get('files_indexed', self._file_count):,}`\n"
                f"- **Failed Files:** `{s.get('files_failed', 0)}`\n"
                f"- **Watched Dirs:** `{', '.join(s.get('watched_dirs', ['Documents/NMIMS']))}`"
            )
        elif root == "/reindex":
            self._mount_system_msg("🔄 Triggering background reindexing of watched directories...")
            self._do_reindex()
        elif root == "/copy":
            self.action_copy_answer()
        elif root in ("/help", "/?"):
            self._mount_system_msg(
                "### RAGA OpenCode TUI Command & Shortcut Reference\n\n"
                "| Command / Key | Description |\n"
                "| :--- | :--- |\n"
                "| `Ctrl + P` | Open searchable **Command Palette** |\n"
                "| `Ctrl + \\\\` | Toggle **Sources Sidebar** |\n"
                "| `Ctrl + Y` | **Copy** latest answer to clipboard |\n"
                "| `Ctrl + L` | **Clear** chat scrollback |\n"
                "| `1` – `5` | **Quick Preview** sources 1 through 5 |\n"
                "| `/themes <name>` | Switch theme (`nord`, `tokyonight`, `catppuccin`, `matrix`...) |\n"
                "| `/reindex` | Force re-index of documents |\n"
                "| `/clear` | Start a new session |\n"
                "| `/status` | View system & indexing telemetry |\n"
                "| `/exit` | Quit RAGA |"
            )
        elif root == "/exit":
            self.exit()
        else:
            self._mount_system_msg(f"Unknown command `{cmd}`. Type `/help` for available commands.")

    def _mount_system_msg(self, markdown_text: str) -> None:
        scroll = self.query_one("#chat-scroll", VerticalScroll)
        card = SystemCard(markdown_text, self.active_theme)
        scroll.mount(card)
        scroll.scroll_end(animate=False)

    @work(thread=True)
    def _do_reindex(self) -> None:
        try:
            import asyncio
            from core.reindex_engine import reindex_directory
            res = asyncio.run(reindex_directory())
            self.call_from_thread(self.notify, f"Reindexing complete: {res.get('processed', 0)} files updated.", timeout=3)
        except Exception as e:
            self.call_from_thread(self.notify, f"Reindexing error: {e}", timeout=3)

    # ── Core Query Execution ───────────────────────────────────────────────────

    @work(thread=True)
    def _do_ask(self, query: str) -> None:
        t_start = time.time()
        from core.query_classifier import classify_query
        qtype = classify_query(query)

        # Update header badge
        self.call_from_thread(self._update_header_badge, qtype)

        # ── Filesystem / Location: Fast direct path, no LLM needed ──
        if qtype in ("filesystem", "location"):
            from core.engine import ask
            result = ask(query)
            text_body = result.get("text", "")
            elapsed = time.time() - t_start
            self._last_answer = text_body
            self._history.append({"role": "user", "content": query})
            self._history.append({"role": "assistant", "content": text_body})
            self._history = self._history[-8:]
            self.call_from_thread(self._set_live_content, text_body)
            self.call_from_thread(self._finalize, result.get("sources", []), [], elapsed)
            return

        # ── Multi-turn Context & @file mentions Resolution ──
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
            elapsed = time.time() - t_start
            self.call_from_thread(self._set_live_content, "Nothing relevant found in your indexed files.")
            self.call_from_thread(self._finalize, [], chunks, elapsed)
            return

        self.call_from_thread(
            self._set_live_content,
            f"*Found {len(chunks)} relevant chunks across your files. Synthesizing answer...*",
        )

        from core.generator import generate_answer_streaming
        buffer = ""
        last_push = time.time()

        for token in generate_answer_streaming(query, chunks, history=self._history):
            buffer += token
            now = time.time()
            if now - last_push >= 0.04:
                snapshot = buffer
                self.call_from_thread(self._set_live_content, snapshot)
                last_push = now

        # Final render with complete Markdown
        elapsed = time.time() - t_start
        self._last_answer = buffer
        self._history.append({"role": "user", "content": query})
        self._history.append({"role": "assistant", "content": buffer})
        self._history = self._history[-8:]

        self.call_from_thread(self._set_live_content, buffer)

        seen: set[str] = set()
        sources: list[str] = []
        for c in chunks:
            if c["file_path"] not in seen:
                seen.add(c["file_path"])
                sources.append(c["file_path"])

        self.call_from_thread(self._finalize, sources, chunks, elapsed)

    # ── Thread-Safe Helpers ───────────────────────────────────────────────────

    def _update_header_badge(self, qtype: str) -> None:
        if self._active_card is not None:
            self._active_card.title_widget.update(_make_raga_header(qtype, self.active_theme))

    def _set_live_content(self, text: str) -> None:
        if self._active_card is not None:
            self._active_card.body_widget.update(Markdown(text))
            self.query_one("#chat-scroll", VerticalScroll).scroll_end(animate=False)

    def _finalize(self, sources: list[str], chunks: list[dict], elapsed: float = 0.0) -> None:
        if self._active_card is not None:
            self._active_card.copy_btn.text_to_copy = self._last_answer
            t_stats = Text()
            t_stats.append(f"⚡ {elapsed:.2f}s · {len(sources)} sources reranked · Qwen 2.5 3B (GPU)", style=self.active_theme.text_subtle)
            self._active_card.stats_widget.update(t_stats)
            self.query_one("#chat-scroll", VerticalScroll).scroll_end(animate=False)
            self._active_card = None

        # Populate sidebar sources
        src_list = self.query_one("#sources-list", ListView)
        src_list.clear()
        self.query_one("#sources-header", Label).update(f"📦 SOURCES ({len(sources[:5])})")

        for i, path in enumerate(sources[:5], 1):
            matched_chunk = next((c for c in chunks if c.get("file_path") == path), None)
            chunk_text = matched_chunk["chunk_text"] if matched_chunk else f"File: {path}"
            score = matched_chunk.get("score", 0.0) if matched_chunk else 0.0
            src_list.append(SourceEntry(i, path, chunk_text, score=score, theme=self.active_theme))

        if not sources:
            src_list.append(ListItem(Static(Text("  No sources referenced", style=self.active_theme.text_subtle))))
            self.query_one("#preview-text", Static).update(Text("No sources found for this query.", style=self.active_theme.text_subtle))
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
            _make_preview_msg(path, snippet, self.active_theme)
        )

    # ── Theme Switching & Dynamic Refresh ─────────────────────────────────────

    def _switch_theme(self, theme_name: str) -> None:
        if theme_name not in THEMES:
            self.notify(f"Unknown theme: {theme_name}", timeout=2)
            return
        self.active_theme = THEMES[theme_name]
        self.config["theme"] = theme_name
        save_config(self.config)

        # Regenerate and apply CSS
        self.CSS = generate_css(self.active_theme)
        stylesheet = Stylesheet(variables=self.get_css_variables())
        for read_from, css, tie_breaker, scope in self._get_default_css():
            stylesheet.add_source(css, read_from=read_from, is_default_css=True, tie_breaker=tie_breaker, scope=scope)
        try:
            app_path = inspect.getfile(self.__class__)
        except (TypeError, OSError):
            app_path = ""
        stylesheet.add_source(self.CSS, read_from=(app_path, f"{self.__class__.__name__}.CSS"), is_default_css=False)
        stylesheet.parse()
        self.stylesheet = stylesheet
        self.stylesheet.update(self)
        for screen in self.screen_stack:
            self.stylesheet.update(screen)
        self.refresh(layout=True)

        # Update statusbar mid
        self.query_one("#statusbar-mid", Static).update(f"📁 {self._file_count:,} files · 🎨 {self.active_theme.name}")
        self.notify(f"Theme switched to: {theme_name.capitalize()}", timeout=2)

    # ── Source Selection & Preview ────────────────────────────────────────────

    @on(ListView.Selected, "#sources-list")
    def on_source_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, SourceEntry):
            self._render_preview(item.source_path, item.chunk_text)

    # ── Keybindings & Actions ─────────────────────────────────────────────────

    def action_command_palette(self) -> None:
        def on_palette_result(action: str) -> None:
            if not action:
                return
            if action.startswith("theme:"):
                theme_name = action.replace("theme:", "")
                self._switch_theme(theme_name)
            elif action == "cmd:reindex":
                self._handle_slash_command("/reindex")
            elif action == "cmd:clear":
                self.action_clear_chat()
            elif action == "cmd:status":
                self._handle_slash_command("/status")
            elif action == "cmd:copy":
                self.action_copy_answer()
            elif action == "cmd:toggle_sidebar":
                self.action_toggle_sources()
            elif action == "cmd:help":
                self._handle_slash_command("/help")
            elif action == "cmd:exit":
                self.exit()

        self.push_screen(CommandPaletteModal(), on_palette_result)

    def action_focus_sources(self) -> None:
        self.query_one("#sources-list", ListView).focus()

    def action_toggle_sources(self) -> None:
        sidebar = self.query_one("#sidebar", Vertical)
        chat = self.query_one("#chat-scroll", VerticalScroll)
        sidebar.display = not sidebar.display
        chat.styles.width = "100%" if not sidebar.display else "63%"

    def action_clear_chat(self) -> None:
        scroll = self.query_one("#chat-scroll", VerticalScroll)
        scroll.remove_children()
        scroll.mount(Static(_make_hero_banner(self._file_count, self.active_theme), id="hero-banner"))
        self._history.clear()
        self.notify("Chat session cleared", timeout=2)

    def action_copy_answer(self) -> None:
        if not self._last_answer:
            self.notify("No answer to copy yet", timeout=2)
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


def run_app() -> None:
    """Launch the RAGA OpenCode-spec TUI Application."""
    app = RagaApp()
    app.run()


if __name__ == "__main__":
    run_app()
