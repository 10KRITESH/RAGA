"""
Ingestion pipeline — consumes SourceEvents from the watcher queue and
runs them through: extract -> chunk -> embed (batched) -> store.
"""
import asyncio
import hashlib
import uuid
from pathlib import Path

from watchers.events import SourceEvent, EventType
from extractors.text import TextExtractor
from extractors.pdf import PDFExtractor
from extractors.image import ImageOCRExtractor
from extractors.media import MediaMetadataExtractor
from extractors.office import OfficeExtractor
from ingestion.chunker import chunk_text
from ingestion.embedder import embed_batch
from storage import metadata_db, vector_store

EXTRACTORS = [
    TextExtractor(),
    PDFExtractor(),
    ImageOCRExtractor(),
    OfficeExtractor(),
    MediaMetadataExtractor(),
]


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
        return

    try:
        text = extractor.extract(path)
    except Exception as e:
        print(f"[failed] {path} - extraction error: {e}")
        return

    if not text.strip():
        return

    content_hash = _hash_content(text)

    existing = metadata_db.get_file(conn, str(path))
    if existing and existing["content_hash"] == content_hash:
        return

    if existing:
        vector_store.delete_chunks_for_file(str(path))

    chunks = chunk_text(text)
    if not chunks:
        print(f"[empty] {path} - no content to index")
        metadata_db.upsert_file(conn, str(path), content_hash, extractor.source_type, 0)
        return

    # Prepare texts for batch embedding with metadata prefixes
    embed_texts = []
    for i, chunk in enumerate(chunks):
        embed_text = f"[File: {path.name} | Type: {extractor.source_type}]\n{chunk}"
        if i == 0:
            embed_text = (
                f"What is the title? Who are the authors? What is this document or file about?\n"
                + embed_text
            )
        embed_texts.append(embed_text)

    # Batch embed all chunks in 1-2 fast requests instead of sequential roundtrips
    vectors = embed_batch(embed_texts)

    rows = []
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        rows.append({
            "chunk_id": str(uuid.uuid4()),
            "file_path": str(path),
            "chunk_text": chunk,
            "chunk_index": i,
            "vector": vector,
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
