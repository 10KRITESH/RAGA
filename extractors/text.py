# Plain text or code file extractor simple one

from pathlib import Path
from extractors.base import Extractor

TEXT_EXTENSIONS = {".txt", ".md", ".py", ".js", ".ts", ".json", ".yaml", ".yml", ".toml", ".sh"}

class TextExtractor(Extractor):
    source_type = "text"

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in TEXT_EXTENSIONS

    def extract(self, path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="ignore")
    