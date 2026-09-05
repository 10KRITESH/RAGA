"""
Media & Binary Metadata Extractor — extracts lightweight metadata for audio, video,
archives, and other binary files so they are searchable by filename, category, path,
and (for archives) internal file listings without decoding heavy media streams.
"""
import zipfile
import tarfile
from pathlib import Path
from extractors.base import Extractor

AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".opus", ".wma"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"}
ARCHIVE_EXTENSIONS = {".zip", ".tar", ".gz", ".7z", ".rar", ".bz2", ".xz", ".tgz"}
PACKAGE_EXTENSIONS = {".iso", ".img", ".deb", ".rpm", ".appimage"}

MEDIA_EXTENSIONS = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS | ARCHIVE_EXTENSIONS | PACKAGE_EXTENSIONS


class MediaMetadataExtractor(Extractor):
    source_type = "media"

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in MEDIA_EXTENSIONS

    def _get_category(self, ext: str) -> str:
        if ext in AUDIO_EXTENSIONS:
            return "audio/music"
        elif ext in VIDEO_EXTENSIONS:
            return "video"
        elif ext in ARCHIVE_EXTENSIONS:
            return "archive/compressed"
        elif ext in PACKAGE_EXTENSIONS:
            return "package/disk-image"
        return "media"

    def _inspect_archive_contents(self, path: Path) -> str:
        """Inspects file listing inside zip / tar archives without extracting."""
        ext = path.suffix.lower()
        file_list = []
        try:
            if ext == ".zip":
                with zipfile.ZipFile(path, "r") as z:
                    file_list = z.namelist()[:30]
            elif ext in {".tar", ".tgz", ".gz", ".bz2", ".xz"}:
                with tarfile.open(path, "r:*") as t:
                    file_list = [m.name for m in t.getmembers()[:30]]
        except Exception:
            pass

        if file_list:
            items_str = "\n".join(f"  - {f}" for f in file_list)
            return f"\nFiles Inside Archive (top {len(file_list)}):\n{items_str}\n"
        return ""

    def extract(self, path: Path) -> str:
        stat = path.stat()
        size_bytes = stat.st_size
        size_mb = size_bytes / (1024 * 1024)
        if size_mb >= 1024:
            size_str = f"{size_mb / 1024:.2f} GB"
        elif size_mb >= 1:
            size_str = f"{size_mb:.2f} MB"
        else:
            size_str = f"{size_bytes / 1024:.1f} KB"

        ext = path.suffix.lower()
        category = self._get_category(ext)
        clean_name = path.stem.replace("_", " ").replace("-", " ").replace(".", " ")

        archive_info = ""
        if ext in ARCHIVE_EXTENSIONS:
            archive_info = self._inspect_archive_contents(path)

        return (
            f"File: {path.name}\n"
            f"Title/Name: {clean_name}\n"
            f"Category: {category}\n"
            f"File Type: {ext}\n"
            f"File Size: {size_str}\n"
            f"Directory: {path.parent}\n"
            f"Full Path: {path.resolve()}\n"
            f"{archive_info}"
            f"Description: {category.capitalize()} file named '{path.name}' stored at '{path}'."
        )
