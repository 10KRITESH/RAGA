"""
Office Document Extractor — extracts text from .docx, .pptx, .xlsx, .odt, .odp
using native zip/XML parsing without heavy external dependencies.
"""
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from extractors.base import Extractor

OFFICE_EXTENSIONS = {".docx", ".pptx", ".xlsx", ".odt", ".odp", ".ods"}


class OfficeExtractor(Extractor):
    source_type = "office"

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in OFFICE_EXTENSIONS

    def extract(self, path: Path) -> str:
        ext = path.suffix.lower()
        try:
            with zipfile.ZipFile(path) as z:
                if ext == ".docx":
                    return self._extract_docx(z)
                elif ext == ".pptx":
                    return self._extract_pptx(z)
                elif ext == ".xlsx":
                    return self._extract_xlsx(z)
                elif ext in {".odt", ".odp", ".ods"}:
                    return self._extract_opendoc(z)
        except Exception:
            return ""
        return ""

    def _extract_docx(self, z: zipfile.ZipFile) -> str:
        if "word/document.xml" not in z.namelist():
            return ""
        xml_content = z.read("word/document.xml")
        tree = ET.fromstring(xml_content)
        texts = [node.text for node in tree.iter() if node.text and node.tag.endswith("t")]
        return "\n".join(texts)

    def _extract_pptx(self, z: zipfile.ZipFile) -> str:
        texts = []
        slide_files = sorted([
            f for f in z.namelist()
            if f.startswith("ppt/slides/slide") and f.endswith(".xml")
        ])
        for idx, slide_file in enumerate(slide_files, start=1):
            xml_content = z.read(slide_file)
            tree = ET.fromstring(xml_content)
            slide_texts = [node.text for node in tree.iter() if node.text and node.tag.endswith("t")]
            if slide_texts:
                texts.append(f"--- Slide {idx} ---\n" + "\n".join(slide_texts))
        return "\n\n".join(texts)

    def _extract_xlsx(self, z: zipfile.ZipFile) -> str:
        if "xl/sharedStrings.xml" not in z.namelist():
            return ""
        xml_content = z.read("xl/sharedStrings.xml")
        tree = ET.fromstring(xml_content)
        texts = [node.text for node in tree.iter() if node.text and node.tag.endswith("t")]
        return "\n".join(texts)

    def _extract_opendoc(self, z: zipfile.ZipFile) -> str:
        if "content.xml" not in z.namelist():
            return ""
        xml_content = z.read("content.xml")
        tree = ET.fromstring(xml_content)
        texts = [node.text for node in tree.iter() if node.text]
        return "\n".join(texts)
