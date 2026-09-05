# Native sliding win chunker (trial) shoud be changed in future

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    # just good ol split and chunking

    if not text.strip():
        return []

    # split text by whitespace
    words = text.split()
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks