# Plain text, code, and config file extractor

from pathlib import Path
from extractors.base import Extractor

TEXT_EXTENSIONS = {
    # Documents / Notes
    ".txt", ".md", ".org", ".rst", ".tex", ".csv",
    # Web / Config / Data
    ".json", ".yaml", ".yml", ".toml", ".xml", ".html", ".css", ".scss",
    ".ini", ".cfg", ".conf", ".env", ".sql",
    # Scripts / Shell
    ".sh", ".bash", ".zsh", ".fish",
    # Code
    ".py", ".js", ".ts", ".jsx", ".tsx", ".rs", ".go", ".c", ".cpp",
    ".h", ".hpp", ".java", ".kt", ".lua", ".zig", ".rb", ".php",
}

# Common extensionless or dot config/build files
KNOWN_EXACT_FILENAMES = {
    "dockerfile", "dockerfile-alpine", "containerfile", "makefile", "gnumakefile",
    "cmakelists.txt", "procfile", "gemfile", "rakefile", "vagrantfile", "brewfile",
    ".dockerignore", ".gitignore", ".env", ".env.example", ".editorconfig",
    "caddyfile", "jenkinsfile"
}

# Max text file size to index (2MB) — skips giant logs / generated minified files
MAX_TEXT_SIZE_BYTES = 2 * 1024 * 1024


class TextExtractor(Extractor):
    source_type = "text"

    def can_handle(self, path: Path) -> bool:
        name_lower = path.name.lower()
        if name_lower in KNOWN_EXACT_FILENAMES or name_lower.startswith("dockerfile."):
            return True
        return path.suffix.lower() in TEXT_EXTENSIONS

    def extract(self, path: Path) -> str:
        if path.stat().st_size > MAX_TEXT_SIZE_BYTES:
            # Read first 50KB summary if giant file
            with path.open("r", encoding="utf-8", errors="ignore") as f:
                return f.read(50_000)
        return path.read_text(encoding="utf-8", errors="ignore")
