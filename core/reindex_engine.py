# Reindex (big one) does all teh indexing inside an existing dir

from pathlib import Path
from watchers.events import SourceEvent, EventType
from ingestion.pipeline import process_event
from storage import metadata_db
from config import EXCLUSIONS
from watchers.filesystem import _matches_exclusion
import asyncio

async def reindex_directory(path: str) -> dict:
    root = Path(path)
    if not root.exists():
        return {"error": f"Path does not exist: {path}"}
    
    conn = metadata_db.get_connection()
    total = 0
    indexed = 0

    for file_path in root.rglob('*'):
        if file_path.is_dir():
            continue
        if _matches_exclusion(str(file_path), EXCLUSIONS):
            continue
        
        total += 1
        event = SourceEvent(path=str(file_path), event_type=EventType.CREATED)
        await process_event(event, conn)
        indexed += 1
    
    return {"total_files": total, "processed": indexed}