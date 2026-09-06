"""
Query Classifier — categorizes a user query into one of three types:

  'filesystem'  → listing/browsing queries ("list folders in X", "what's in X")
  'location'    → find/where queries ("where are my X", "find my X notes")
  'content'     → everything else → full RAG pipeline

Keeps query routing logic out of the main engine.
"""
import re

# Patterns for directory/file listing queries.
# Must strongly imply the user wants a directory/folder listing, not content.
_FS_PATTERNS = [
    # list/show/display ... folders/files/directories/contents
    r"\b(list|show|display|enumerate)\b.{0,50}\b(folder|folders|directory|directories|contents?|items?)\b",
    # "list files in X" (but NOT "list experiments" — experiment ≠ filesystem concept)
    r"\b(list|show)\b.{0,30}\bfiles\b.{0,30}\b(in|inside|under|within)\b",
    # "what folders are in X", "what directories are in X"
    r"\bwhat\b.{0,15}(folder|directory|directories|folders)\b.{0,30}\b(in|inside|under|within|present|there)\b",
    # "what's in X folder / directory" — must explicitly say folder/directory
    r"\bwhat.{0,5}(is|are|s)\b.{0,15}in\b.{0,40}\b(folder|directory)\b",
    # bare ls/dir commands
    r"^\s*(ls|dir)\b",
]

# Patterns for "find / where is X" queries
_LOC_PATTERNS = [
    r"\bwhere\b.{0,60}\b(is|are|did|can|do|was|were)\b",
    r"\bwhere\b.{0,10}\b(my|the|are|is)\b",
    r"\bfind\b.{0,10}\b(my|the|all)\b",
    r"\blocate\b",
    r"\blook\s+for\b",
]


def classify_query(query: str) -> str:
    """
    Returns 'filesystem', 'location', or 'content'.
    Order matters: filesystem is checked first (more specific).
    """
    q = query.lower().strip()

    for pat in _FS_PATTERNS:
        if re.search(pat, q):
            return "filesystem"

    for pat in _LOC_PATTERNS:
        if re.search(pat, q):
            return "location"

    return "content"
