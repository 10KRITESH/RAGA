"""
OpenCode-spec Theme System for RAGA TUI.
Supports Nord (default), OpenCode, Tokyo Night, Catppuccin, Gruvbox, One Dark, Matrix.
Persists settings to ~/.config/raga/tui.json.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Theme:
    name: str
    bg_base: str
    bg_panel: str
    bg_surface: str
    bg_element: str
    bg_input: str
    border: str
    border_active: str
    border_subtle: str
    text: str
    text_muted: str
    text_subtle: str
    primary: str
    secondary: str
    tertiary: str
    accent: str
    success: str
    warning: str
    error: str


THEMES: dict[str, Theme] = {
    "nord": Theme(
        name="nord",
        bg_base="#2E3440",
        bg_panel="#3B4252",
        bg_surface="#434C5E",
        bg_element="#4C566A",
        bg_input="#3B4252",
        border="#434C5E",
        border_active="#88C0D0",
        border_subtle="#3B4252",
        text="#ECEFF4",
        text_muted="#D8DEE9",
        text_subtle="#4C566A",
        primary="#88C0D0",       # Frost Cyan
        secondary="#81A1C1",     # Frost Blue
        tertiary="#B48EAD",      # Frost Purple
        accent="#8FBCBB",
        success="#A3BE8C",       # Aurora Green
        warning="#EBCB8B",       # Aurora Yellow
        error="#BF616A",         # Aurora Red
    ),
    "opencode": Theme(
        name="opencode",
        bg_base="#0D1117",
        bg_panel="#161B22",
        bg_surface="#21262D",
        bg_element="#30363D",
        bg_input="#161B22",
        border="#30363D",
        border_active="#58A6FF",
        border_subtle="#21262D",
        text="#F0F6FC",
        text_muted="#8B949E",
        text_subtle="#484F58",
        primary="#58A6FF",
        secondary="#79C0FF",
        tertiary="#BC8CFF",
        accent="#58A6FF",
        success="#3FB950",
        warning="#D29922",
        error="#F85149",
    ),
    "tokyonight": Theme(
        name="tokyonight",
        bg_base="#1A1B26",
        bg_panel="#24283B",
        bg_surface="#2F354F",
        bg_element="#414868",
        bg_input="#24283B",
        border="#414868",
        border_active="#7AA2F7",
        border_subtle="#2F354F",
        text="#C0CAF5",
        text_muted="#7AA2F7",
        text_subtle="#565F89",
        primary="#7AA2F7",
        secondary="#7DCFFF",
        tertiary="#BB9AF7",
        accent="#2AC3DE",
        success="#9ECE6A",
        warning="#E0AF68",
        error="#F7768E",
    ),
    "catppuccin": Theme(
        name="catppuccin",
        bg_base="#1E1E2E",
        bg_panel="#181825",
        bg_surface="#313244",
        bg_element="#45475A",
        bg_input="#181825",
        border="#313244",
        border_active="#89B4FA",
        border_subtle="#26283B",
        text="#CDD6F4",
        text_muted="#A6ADC8",
        text_subtle="#6C7086",
        primary="#89B4FA",
        secondary="#89DCEB",
        tertiary="#CBA6F7",
        accent="#F5C2E7",
        success="#A6E3A1",
        warning="#F9E2AF",
        error="#F38BA8",
    ),
    "gruvbox": Theme(
        name="gruvbox",
        bg_base="#282828",
        bg_panel="#3C3836",
        bg_surface="#504945",
        bg_element="#665C54",
        bg_input="#3C3836",
        border="#504945",
        border_active="#83A598",
        border_subtle="#3C3836",
        text="#EBDBB2",
        text_muted="#D5C4A1",
        text_subtle="#928374",
        primary="#83A598",
        secondary="#8EC07C",
        tertiary="#D3869B",
        accent="#FE8019",
        success="#B8BB26",
        warning="#FABD2F",
        error="#FB4934",
    ),
    "one-dark": Theme(
        name="one-dark",
        bg_base="#282C34",
        bg_panel="#21252B",
        bg_surface="#2C313A",
        bg_element="#3E4451",
        bg_input="#21252B",
        border="#3E4451",
        border_active="#61AFEF",
        border_subtle="#2C313A",
        text="#ABB2BF",
        text_muted="#828997",
        text_subtle="#5C6370",
        primary="#61AFEF",
        secondary="#56B6C2",
        tertiary="#C678DD",
        accent="#98C379",
        success="#98C379",
        warning="#E5C07B",
        error="#E06C75",
    ),
    "matrix": Theme(
        name="matrix",
        bg_base="#0D1117",
        bg_panel="#161B22",
        bg_surface="#21262D",
        bg_element="#30363D",
        bg_input="#161B22",
        border="#30363D",
        border_active="#00FF66",
        border_subtle="#21262D",
        text="#E6EDF3",
        text_muted="#7EE787",
        text_subtle="#00AA44",
        primary="#00FF66",
        secondary="#33FF77",
        tertiary="#00DD55",
        accent="#00FF66",
        success="#00FF66",
        warning="#FFEE00",
        error="#FF3333",
    ),
}

CONFIG_DIR = Path.home() / ".config" / "raga"
CONFIG_FILE = CONFIG_DIR / "tui.json"


def load_config() -> dict:
    """Load configuration from ~/.config/raga/tui.json with safe defaults."""
    default = {
        "$schema": "https://opencode.ai/tui.json",
        "theme": "nord",
        "animations": True,
        "leader_key": "ctrl+x",
        "cursor": "block",
        "scroll_speed": 1.0,
    }
    if not CONFIG_FILE.exists():
        return default
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        default.update(data)
        return default
    except Exception:
        return default


def save_config(config: dict) -> None:
    """Save configuration to ~/.config/raga/tui.json."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")
    except Exception:
        pass


def get_theme(name: str | None = None) -> Theme:
    """Get active Theme instance."""
    if not name:
        cfg = load_config()
        name = cfg.get("theme", "nord")
    return THEMES.get(name.lower(), THEMES["nord"])


def generate_css(theme: Theme) -> str:
    """Generate dynamic Textual CSS for OpenCode TUI layout."""
    return f"""
    Screen {{
        background: {theme.bg_base};
        color: {theme.text};
    }}

    /* ── Minimalist Slim Scrollbars ── */
    VerticalScroll, ListView, OptionList, #preview-area, #palette-list {{
        scrollbar-size: 1 1;
        scrollbar-color: {theme.border} {theme.bg_base};
        scrollbar-color-hover: {theme.primary} {theme.bg_base};
        scrollbar-color-active: {theme.primary} {theme.bg_base};
    }}

    /* ── Top Header / Session Tabs ── */
    #session-bar {{
        height: 3;
        background: {theme.bg_panel};
        border-bottom: solid {theme.border};
        layout: horizontal;
        padding: 0 1;
    }}
    .session-tab {{
        width: auto;
        color: {theme.primary};
        text-style: bold;
        content-align: left middle;
        padding-right: 2;
    }}
    .session-meta {{
        width: auto;
        color: {theme.text_subtle};
        content-align: left middle;
    }}
    .session-status {{
        width: 1fr;
        color: {theme.success};
        content-align: right middle;
        text-align: right;
    }}

    /* ── Main 3-Section Container ── */
    #main-container {{
        height: 1fr;
        padding: 0;
    }}

    /* ── Left Transcript (Scrollback) ── */
    #chat-scroll {{
        width: 63%;
        background: {theme.bg_base};
        border-right: solid {theme.border};
        padding: 1 2;
    }}

    /* ── User & Assistant Cards ── */
    UserCard {{
        height: auto;
        background: {theme.bg_panel};
        border: solid {theme.border};
        border-left: solid {theme.primary};
        padding: 1 2;
        margin: 1 0;
    }}

    RagaCard, SystemCard, .raga-card {{
        height: auto;
        background: {theme.bg_panel};
        border: solid {theme.border};
        border-left: solid {theme.tertiary};
        padding: 1 2;
        margin: 1 0;
    }}

    .card-header-row {{
        height: 1;
        layout: horizontal;
        margin-bottom: 1;
    }}

    .card-title {{
        width: 1fr;
    }}

    .card-body {{
        height: auto;
        padding-top: 1;
    }}

    .card-stats {{
        height: auto;
        color: {theme.text_subtle};
        padding-top: 1;
        border-top: solid {theme.border_subtle};
        margin-top: 1;
    }}

    /* ── Thinking / Tool Execution Block ── */
    .thinking-box {{
        background: {theme.bg_base};
        border: solid {theme.border};
        padding: 0 1;
        margin: 0 0 1 0;
        color: {theme.text_muted};
    }}

    /* ── Right Context / Sources Sidebar ── */
    #sidebar {{
        width: 37%;
        background: {theme.bg_panel};
        padding: 1 1;
        layout: vertical;
    }}
    #sources-header {{
        color: {theme.primary};
        text-style: bold;
        height: 1;
        margin-bottom: 1;
        padding-left: 1;
    }}
    #sources-list {{
        height: 48%;
        background: {theme.bg_base};
        border: round {theme.border};
    }}
    #sources-list > ListItem {{
        padding: 0 1;
        height: auto;
        border-bottom: solid {theme.border_subtle};
    }}
    #sources-list > ListItem:hover {{
        background: {theme.bg_surface};
    }}
    #sources-list > ListItem.--highlight {{
        background: {theme.bg_surface};
        border-left: solid {theme.primary};
    }}

    #preview-header {{
        color: {theme.text_muted};
        text-style: bold;
        height: 1;
        margin-top: 1;
        margin-bottom: 0;
        padding-left: 1;
    }}
    #preview-area {{
        height: 1fr;
        background: {theme.bg_base};
        border: round {theme.border};
        padding: 1 1;
        overflow-y: auto;
    }}

    /* ── Split-Footer Area ── */
    #footer-stack {{
        height: auto;
        layout: vertical;
        background: {theme.bg_panel};
        border-top: solid {theme.border};
    }}

    /* ── Autocomplete Popup Menu ── */
    #autocomplete-popup {{
        height: 7;
        max-height: 7;
        background: {theme.bg_surface};
        border: round {theme.border_active};
        margin: 0 1;
        display: none;
    }}
    #autocomplete-options {{
        height: 1fr;
        background: {theme.bg_surface};
        border: none;
    }}
    #autocomplete-options > .option-list--option-highlighted {{
        background: {theme.primary};
        color: {theme.bg_base};
    }}

    /* ── Input Box (Composer) ── */
    #input-container {{
        height: 3;
        background: {theme.bg_input};
        padding: 0 1;
    }}
    #query-input {{
        width: 100%;
        height: 3;
        background: {theme.bg_input};
        border: none;
        color: {theme.text};
        padding: 0 1;
    }}
    #query-input:focus {{
        border: none;
    }}

    /* ── Statusbar Line ── */
    #statusbar {{
        height: 1;
        background: {theme.bg_base};
        border-top: solid {theme.border_subtle};
        layout: horizontal;
        padding: 0 1;
    }}
    .statusbar-left {{
        width: auto;
        color: {theme.primary};
        text-style: bold;
    }}
    .statusbar-mid {{
        width: 1fr;
        color: {theme.text_subtle};
        padding-left: 2;
    }}
    .statusbar-right {{
        width: auto;
        color: {theme.text_subtle};
        text-align: right;
    }}

    /* ── Command Palette Modal ── */
    #palette-modal {{
        align: center middle;
    }}
    #palette-dialog {{
        width: 65;
        height: 18;
        background: {theme.bg_panel};
        border: double {theme.border_active};
        padding: 1 2;
    }}
    #palette-title {{
        color: {theme.primary};
        text-style: bold;
        height: 1;
        margin-bottom: 1;
    }}
    #palette-input {{
        width: 100%;
        height: 3;
        background: {theme.bg_input};
        border: round {theme.border};
        color: {theme.text};
        margin-bottom: 1;
    }}
    #palette-list {{
        height: 1fr;
        background: {theme.bg_base};
        border: round {theme.border};
    }}
    #palette-list > ListItem {{
        padding: 0 1;
        height: 1;
    }}
    #palette-list > ListItem:hover, #palette-list > ListItem.--highlight {{
        background: {theme.primary};
        color: {theme.bg_base};
    }}
    """
