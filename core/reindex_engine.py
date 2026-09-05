"""
Reindex Engine — scans a directory and indexes files concurrently in batches,
rebuilding the full-text search index once at the end.
"""
import asyncio
from pathlib import Path
from watchers.events import SourceEvent, EventType
from ingestion.pipeline import process_event
from storage import metadata_db, vector_store
from config import EXCLUSIONS
from watchers.filesystem import _matches_exclusion


async def reindex_directory(path: str, concurrency: int = 8) -> dict:
    root = Path(path).resolve()
    if not root.exists():
        return {"error": f"Path does not exist: {path}"}

    conn = metadata_db.get_connection()
    all_files: list[Path] = []

    # 1. Discover all non-excluded files
    for file_path in root.rglob('*'):
        if file_path.is_dir():
            continue
        if _matches_exclusion(str(file_path), EXCLUSIONS):
            continue
        all_files.append(file_path)

    total = len(all_files)
    if total == 0:
        return {"total_files": 0, "processed": 0}

    # 2. Process files concurrently with worker pool
    sem = asyncio.Semaphore(concurrency)
    processed_count = 0

    async def _worker(fp: Path):
        nonlocal processed_count
        async with sem:
            event = SourceEvent(path=str(fp), event_type=EventType.CREATED)
            try:
                await process_event(event, conn)
            except Exception as e:
                print(f"[failed] {fp} - {e}")
            processed_count += 1

    # Run all workers concurrently
    await asyncio.gather(*[_worker(fp) for fp in all_files])

    # 3. Rebuild FTS index ONCE after the entire batch is in LanceDB
    vector_store.rebuild_fts()

    return {"total_files": total, "processed": processed_count}
