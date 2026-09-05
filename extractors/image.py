# Image OCR using Tesseract
from pytesseract import pytesseract
from pathlib import Path
import pytesseract
from PIL import Image 
from extractors.base import Extractor

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

class ImageOCRExtractor(Extractor):
    source_type = "image"

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in IMAGE_EXTENSIONS
    
    def extract(self, path: Path) -> str:
        image = Image.open(path)
        return pytesseract.image_to_string(image)