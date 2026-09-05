"""
SQLite metadata store — tracks indexed files (see Database Design doc,
`files` table).
"""
import sqlite3
from pathlib import Path
from config import SQLITE_PATH

def get_connection() -> sqlite3.Connection:
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SQLITE_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            content_hash TEXT NOT NULL,
            source_type TEXT NOT NULL,
            chunk_count INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'indexed'
        )
    """)
    return conn

def upsert_file(conn: sqlite3.Connection, path: str, content_hash: str, source_type: str, chunk_count: int):
    conn.execute("""
        INSERT INTO files (path, content_hash, source_type, chunk_count, status)
        VALUES (?, ?, ?, ?, 'indexed')
        ON CONFLICT(path) DO UPDATE SET
            content_hash = excluded.content_hash,
            chunk_count = excluded.chunk_count,
            status = 'indexed'
    """, (path, content_hash, source_type, chunk_count))
    conn.commit()

def get_file(conn: sqlite3.Connection, path: str) -> sqlite3.Row | None:
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT * FROM files WHERE path = ?", (path,))
    return cursor.fetchone()

def delete_file(conn: sqlite3.Connection, path: str):
    conn.execute("DELETE FROM files WHERE path = ?", (path,))
    conn.commit()
    