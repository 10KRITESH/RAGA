from config import WATCHED_DIRS
from storage import metadata_db

def get_status() -> dict:
    conn = metadata_db.get_connection()
    return {
        "watched_dirs": WATCHED_DIRS,
        "files_indexed": metadata_db.count_by_status(conn, "indexed"),
        "files_failed": metadata_db.count_by_status(conn, "failed"),
        "last_indexed_at": metadata_db.most_recent_indexed_at(conn)
    }