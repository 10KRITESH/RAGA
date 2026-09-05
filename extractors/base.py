"""
Base interface all content extractors implement — lets the ingestion
pipeline treat every file type the same way (see Extractor Registry
pattern in System Design doc).
"""
from abc import ABC, abstractmethod
from pathlib import Path


class Extractor(ABC):
    source_type: str = "text"  # subclasses override this

    @abstractmethod
    def can_handle(self, path: Path) -> bool:
        """Return True if this extractor knows how to read this file type."""
        ...

    @abstractmethod
    def extract(self, path: Path) -> str:
        """Return the file's text content."""
        ...