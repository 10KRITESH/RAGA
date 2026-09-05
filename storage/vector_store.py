# LanceDB vector store | stores content chunks + embeddings for similarity search

import lancedb
import pyarrow as pa
from config import LANCEDB_PATH

_db = lancedb.connect(str(LANCEDB_PATH))

_SCHEMA = pa.schema([
    pa.field("chunk_id", pa.string()),
    pa.field("file_path", pa.string()),
    pa.field("chunk_text", pa.string()),
    pa.field("chunk_index", pa.int32()),
    pa.field("vector", pa.list_(pa.float32(), 768)),  # nomic-embed-text dimension
    pa.field("source_type", pa.string()),
])

def get_table():
    if "chunks" in _db.table_names():
        table = _db.open_table("chunks")
    else:
        table = _db.create_table("chunks", schema=_SCHEMA)
    return table

def _rebuild_fts(table):
    """Rebuild the FTS index — called after any add/delete."""
    try:
        table.create_fts_index("chunk_text", replace=True)
    except Exception:
        pass

def add_chunks(rows: list[dict]):
    table = get_table()
    table.add(rows)
    _rebuild_fts(table)

def delete_chunks_for_file(file_path: str):
    table = get_table()
    table.delete(f"file_path = '{file_path}'")
    _rebuild_fts(table)
