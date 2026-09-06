"""
Global RAGA settings and constants.
"""
from pathlib import Path

WATCHED_DIRS: list[str] = [
    str(Path.home())
]

EXCLUSIONS: list[str] = [
    # --- Security & Credentials (Privacy First) ---
    "**/.ssh/**",
    "**/.gnupg/**",
    "**/.pki/**",
    "**/.password-store/**",
    "**/.aws/**",
    "**/.azure/**",
    "**/.kube/**",
    "**/.docker/**",

    # --- System & Application Caches / Runtimes ---
    "**/.cache/**",
    "**/tmp/**",
    "**/.tmp/**",
    "**/.temp/**",
    "**/.local/share/Trash/**",
    "**/.local/share/raga/**",
    "**/.local/share/Steam/**",
    "**/.steam/**",
    "**/.wine/**",
    "**/.var/app/**",
    "**/.local/share/flatpak/**",
    "**/.mozilla/**",
    "**/.config/google-chrome/**",
    "**/.config/chromium/**",
    "**/.config/BraveSoftware/**",
    "**/.config/discord/**",
    "**/.config/Slack/**",
    "**/.config/Spotify/**",

    # --- Language / Package Manager Caches & Runtimes ---
    "**/node_modules/**",
    "**/.npm/**",
    "**/.pnpm/**",
    "**/.yarn/**",
    "**/.bun/**",
    "**/.cargo/**",
    "**/.rustup/**",
    "**/.gradle/**",
    "**/.m2/**",
    "**/.pub-cache/**",
    "**/.local/share/uv/**",
    "**/.local/share/virtualenvs/**",

    # --- Python Virtualenvs & Caches ---
    "**/__pycache__/**",
    "**/.venv/**",
    "**/venv/**",
    "**/env/**",
    "**/.pytest_cache/**",
    "**/.mypy_cache/**",
    "**/.ruff_cache/**",
    "**/.tox/**",
    "**/site-packages/**",

    # --- Web Framework Build Artifacts & Manifests ---
    "**/.next/**",
    "**/.nuxt/**",
    "**/.turbo/**",
    "**/.svelte-kit/**",
    "**/.astro/**",

    # --- Build Artifacts & VCS ---
    "**/.git/**",
    "**/.svn/**",
    "**/.hg/**",
    "**/dist/**",
    "**/build/**",
    "**/target/**",       # Rust / Cargo build outputs
    "**/out/**",
    "**/.vscode/**",
    "**/.idea/**",
    "**/.gemini/**",
    "**/.antigravity/**",

    # --- Generated / Asset Video Frames (Prevents OCR choking) ---
    "**/frames/**",

    # --- Self-Exclusion ---
    "**/Documents/NMIMS/projects/RAGA/**",
]

DATA_DIR = Path.home() / ".local" / "share" / "raga"
LANCEDB_PATH = DATA_DIR / "lancedb"
SQLITE_PATH = DATA_DIR / "metadata.sqlite"

EMBEDDING_MODEL = "nomic-embed-text"
GENERATION_MODEL_DEFAULT = "qwen2.5:3b"
GENERATION_MODEL_CODE = "qwen2.5-coder:3b"
OLLAMA_HOST = "http://127.0.0.1:11434"
