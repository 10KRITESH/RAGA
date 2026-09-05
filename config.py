"""
Global RAGA settings and constants.
"""
from pathlib import Path
WATCHED_DIRS: list[str] = [
    str(Path.home() / "Documents")
    ]

EXCLUSIONS: list[str] = [
    "**/.ssh/**",
    "**/.gnupg/**",
    "**/.mozilla/**",
    "**/.cache/**",
    "**/.local/share/raga/**",   # don't index RAGA's own database
    "**/node_modules/**",
    "**/.git/**",
    "**/__pycache__/**",
    "**/.venv/**",
    "**/venv/**",
    "**/Documents/NMIMS/projects/RAGA/**",  # don't index RAGA's own source code
]

DATA_DIR = Path.home() / ".local" / "share" / "raga"
LANCEDB_PATH = DATA_DIR / "lancedb"
SQLITE_PATH = DATA_DIR / "metadata.sqlite"

EMBEDDING_MODEL = "nomic-embed-text"
GENERATION_MODEL_DEFAULT = "llama3.2:3b"
GENERATION_MODEL_CODE = "qwen2.5-coder:7b"
OLLAMA_HOST = "http://127.0.0.1:11434"

