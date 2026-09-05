"""Quick diagnostic: run OCR on a single file and print the raw extracted text."""
import sys
from pathlib import Path
from extractors.image import ImageOCRExtractor

path = Path(sys.argv[1])
extractor = ImageOCRExtractor()
text = extractor.extract(path)

print(f"--- Extracted {len(text)} characters ---")
print(text)