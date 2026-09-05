# ummm Pdf text extractor straight up
from pathlib import Path
import pymupdf as fitz # um PyMuPDF ka import name
from extractors.base import Extractor

class PDFExtractor (Extractor):
    source_type = "pdf"

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"
    
    def extract(self, path: Path) -> str:
        text_parts = []
        with fitz.open(path) as doc:
            for page in doc:
                text_parts.append(page.get_text())
        return "\n".join(text_parts)
    