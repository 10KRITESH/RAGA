"""
Ingestion pipeline — consumes SourceEvents from the watcher queue and
runs them through: extract -> chunk -> embed -> store.
"""
import asyncio
import hashlib
import uuid
from pathlib import Path

from watchers.events import SourceEvent, EventType
from extractors.text import TextExtractor
from extractors.pdf import PDFExtractor
from extractors.image import ImageOCRExtractor
from ingestion.chunker import chunk_text
from ingestion.embedder import embed
from storage import metadata_db, vector_store

EXTRACTORS = [TextExtractor(), PDFExtractor(), ImageOCRExtractor()]


def _hash_content(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _pick_extractor(path: Path):
    for extractor in EXTRACTORS:
        if extractor.can_handle(path):
            return extractor
    return None


async def process_event(event: SourceEvent, conn):
    path = Path(event.path)

    if event.event_type == EventType.DELETED:
        vector_store.delete_chunks_for_file(str(path))
        metadata_db.delete_file(conn, str(path))
        print(f"[deleted] {path}")
        return

    extractor = _pick_extractor(path)
    if extractor is None:
        print(f"[skipped] {path} - unsupported file type")
        return

    try:
        text = extractor.extract(path)
    except Exception as e:
        print(f"[failed] {path} - extraction error: {e}")
        return

    content_hash = _hash_content(text)

    existing = metadata_db.get_file(conn, str(path))
    if existing and existing["content_hash"] == content_hash:
        print(f"[unchanged] {path} - skipping")
        return

    if existing:
        vector_store.delete_chunks_for_file(str(path))

    chunks = chunk_text(text)
    if not chunks:
        print(f"[empty] {path} - no content to index")
        metadata_db.upsert_file(conn, str(path), content_hash, extractor.source_type, 0)
        return

    rows = []
    for i, chunk in enumerate(chunks):
        rows.append({
            "chunk_id": str(uuid.uuid4()),
            "file_path": str(path),
            "chunk_text": chunk,
            "chunk_index": i,
            "vector": embed(chunk),
            "source_type": extractor.source_type,
        })

    vector_store.add_chunks(rows)
    metadata_db.upsert_file(conn, str(path), content_hash, extractor.source_type, len(chunks))
    print(f"[indexed] {path} - {len(chunks)} chunk(s) [{extractor.source_type}]")


async def run_pipeline(queue: asyncio.Queue):
    conn = metadata_db.get_connection()
    while True:
        event = await queue.get()
        await process_event(event, conn)
        queue.task_done()