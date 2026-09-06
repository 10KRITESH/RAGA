"""
Filesystem Engine — handles two query types that bypass RAG entirely:

  handle_filesystem_query(query)
      → Lists contents of a resolved directory (like `ls` but smart)

  handle_location_query(query)
      → Finds files/folders related to a topic using LanceDB path matching
        and returns a structured directory listing without LLM hallucination
"""
import os
import re
from pathlib import Path

from config import WATCHED_DIRS

_HOME = Path.home()

# ------------------------------------------------------------------
# Known folder aliases → absolute paths (longest match wins)
# ------------------------------------------------------------------
KNOWN_PATHS: dict[str, Path] = {
    # Top-level
    "home":         _HOME,
    "documents":    _HOME / "Documents",
    "downloads":    _HOME / "Downloads",
    "desktop":      _HOME / "Desktop",
    "music":        _HOME / "Music",
    "pictures":     _HOME / "Pictures",
    "videos":       _HOME / "Videos",
    # NMIMS
    "nmims":        _HOME / "Documents" / "NMIMS",
    "sem vii":      _HOME / "Documents" / "NMIMS" / "SEM VII",
    "sem vi":       _HOME / "Documents" / "NMIMS" / "SEM VI",
    "sem v":        _HOME / "Documents" / "NMIMS" / "SEM V",
    "capstone":     _HOME / "Documents" / "NMIMS" / "CAPSTONE",
    "projects":     _HOME / "Documents" / "NMIMS" / "projects",
    "aws material": _HOME / "Documents" / "NMIMS" / "AWS Material",
    "aws":          _HOME / "Documents" / "NMIMS" / "AWS Material",
    "hackathon":    _HOME / "Documents" / "NMIMS" / "HACKATHON",
    "saa notes":    _HOME / "Documents" / "NMIMS" / "SAA NOTES",
    "nptel":        _HOME / "Documents" / "NMIMS" / "NPTEL",
    # Subject shortcuts
    "cn":  _HOME / "Documents" / "NMIMS" / "SEM VII" / "CN",
    "eh":  _HOME / "Documents" / "NMIMS" / "SEM VII" / "EH",
    "ds":  _HOME / "Documents" / "NMIMS" / "SEM VII" / "DS",
    "iot": _HOME / "Documents" / "NMIMS" / "SEM VII" / "IOT",
    "os":  _HOME / "Documents" / "NMIMS" / "SEM VII" / "OS",
    "ml":  _HOME / "Documents" / "NMIMS" / "SEM VI" / "ML",
    "cs":  _HOME / "Documents" / "NMIMS" / "SEM VI" / "CS",
    "dc":  _HOME / "Documents" / "NMIMS" / "SEM VI" / "DC",
    "bm":  _HOME / "Documents" / "NMIMS" / "SEM VI" / "BM",
    "ai":  _HOME / "Documents" / "NMIMS" / "SEM V" / "AI",
    "se":  _HOME / "Documents" / "NMIMS" / "SEM V" / "SE",
}


def _resolve_path(query: str) -> Path | None:
    """Extract and resolve a folder path from a natural-language query."""
    q = query.lower()

    # 1. Try known aliases (longest match first to avoid "sem" before "sem vii")
    for alias in sorted(KNOWN_PATHS, key=len, reverse=True):
        if alias in q:
            p = KNOWN_PATHS[alias]
            if p.exists():
                return p

    # 2. Try to find a capitalized word that matches a real dir in watched dirs
    words = re.findall(r"[A-Za-z][A-Za-z0-9 _-]*", query)
    for watched in WATCHED_DIRS:
        for word in sorted(words, key=len, reverse=True):
            candidate = Path(watched) / word.strip()
            if candidate.exists() and candidate.is_dir():
                return candidate

    return None


def _format_dir_listing(path: Path) -> str:
    """Return a clean formatted listing of a directory."""
    try:
        entries = sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
    except PermissionError:
        return f"Permission denied: {path}"

    folders = [e for e in entries if e.is_dir()]
    files   = [e for e in entries if e.is_file()]

    lines = [f"Contents of  {path}/\n"]

    if folders:
        lines.append(f"📁 Folders ({len(folders)}):")
        for f in folders:
            lines.append(f"   {f.name}/")

    if files:
        lines.append(f"\n📄 Files ({len(files)}):")
        for f in files[:30]:
            size = f.stat().st_size
            if size >= 1_048_576:
                sz = f"{size/1_048_576:.1f} MB"
            elif size >= 1024:
                sz = f"{size/1024:.0f} KB"
            else:
                sz = f"{size} B"
            lines.append(f"   {f.name}  ({sz})")
        if len(files) > 30:
            lines.append(f"   ... and {len(files) - 30} more files")

    return "\n".join(lines)


def handle_filesystem_query(query: str) -> dict | None:
    """
    Handle 'list folders in X / what's in X' queries.
    Returns None if the path can't be resolved (falls back to RAG).
    """
    path = _resolve_path(query)
    if path is None:
        return None

    text = _format_dir_listing(path)
    return {"text": text, "sources": [str(path)]}


def handle_location_query(query: str) -> dict | None:
    """
    Handle 'where are my X / find my X' queries.
    Uses LanceDB path matching to find relevant files, deduplicates to
    unique directories, and returns a structured listing WITHOUT going
    through the LLM (which tends to hallucinate content descriptions).
    Returns None if nothing found (falls back to content RAG).
    """
    from storage import vector_store
    from core.retriever import _extract_path_patterns

    table = vector_store.get_table()
    path_patterns = _extract_path_patterns(query)

    if not path_patterns:
        return None

    where_clause = " OR ".join(path_patterns[:15])
    try:
        results = table.search().where(where_clause).limit(200).to_list()
    except Exception:
        return None

    if not results:
        return None

    # Group unique filenames by parent directory
    dir_files: dict[str, list[str]] = {}
    for r in results:
        fp = r["file_path"]
        parent = str(Path(fp).parent)
        fname = Path(fp).name
        if parent not in dir_files:
            dir_files[parent] = []
        if fname not in dir_files[parent]:
            dir_files[parent].append(fname)

    if not dir_files:
        return None

    # Build response
    lines = ["Here's what I found:\n"]
    for folder in sorted(dir_files):
        files = sorted(dir_files[folder])
        lines.append(f"📁 {folder}/")
        for f in files[:10]:
            lines.append(f"   • {f}")
        if len(files) > 10:
            lines.append(f"   ... and {len(files) - 10} more")
        lines.append("")

    text = "\n".join(lines).strip()

    # Unique source paths
    seen: set[str] = set()
    sources = []
    for r in results:
        if r["file_path"] not in seen:
            seen.add(r["file_path"])
            sources.append(r["file_path"])

    return {"text": text, "sources": sources[:15]}
