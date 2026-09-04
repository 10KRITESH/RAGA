# 06 — Database Design

RAGA uses two local data stores, each suited to a different query pattern —
see System Design Section 3.3 for the rationale. This document specifies
their schemas.

## 1. Metadata DB — SQLite

Path: `~/.local/share/raga/metadata.sqlite`

### Table: `files`
Tracks every file RAGA has indexed — one row per file (not per chunk).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal file ID |
| `path` | TEXT | UNIQUE NOT NULL | Absolute filesystem path |
| `content_hash` | TEXT | NOT NULL | Hash of file content, used for dedup |
| `source_type` | TEXT | NOT NULL | `text`, `code`, `pdf`, `image` |
| `size_bytes` | INTEGER | NOT NULL | File size at last index |
| `mtime` | TIMESTAMP | NOT NULL | File's last-modified time (from OS) |
| `indexed_at` | TIMESTAMP | NOT NULL | When RAGA last indexed this file |
| `chunk_count` | INTEGER | NOT NULL DEFAULT 0 | Number of chunks stored in LanceDB for this file |
| `status` | TEXT | NOT NULL DEFAULT 'indexed' | `indexed`, `failed`, `pending` |
| `error_message` | TEXT | NULL | Populated when `status = failed` |

Indexes:
- `UNIQUE INDEX idx_files_path ON files(path)`
- `INDEX idx_files_status ON files(status)` — supports `raga status` queries
  for pending/failed counts

### Table: `watched_dirs`
Tracks which directories are actively being watched by the daemon.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal ID |
| `path` | TEXT | UNIQUE NOT NULL | Absolute directory path |
| `added_at` | TIMESTAMP | NOT NULL | When this directory was added to watch scope |
| `enabled` | BOOLEAN | NOT NULL DEFAULT 1 | Allows disabling without removing config |

### Table: `exclusions`
Directory/pattern exclusions applied within watched directories (e.g.
`node_modules`, `.git`).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal ID |
| `pattern` | TEXT | UNIQUE NOT NULL | Glob-style exclusion pattern |
| `added_at` | TIMESTAMP | NOT NULL | When this exclusion was added |

### Table: `daemon_log` (operational/status support)
Lightweight event log backing `raga status` — not a general application log.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal ID |
| `event_type` | TEXT | NOT NULL | `started`, `stopped`, `crash_recovered`, `reindex_triggered` |
| `detail` | TEXT | NULL | Free-text detail (e.g. path for reindex events) |
| `occurred_at` | TIMESTAMP | NOT NULL | When the event occurred |

Indexes:
- `INDEX idx_daemon_log_occurred_at ON daemon_log(occurred_at DESC)` —
  supports "last update: X seconds ago" in `raga status`

## 2. Vector DB — LanceDB

Path: `~/.local/share/raga/lancedb/`

### Table: `chunks`
One row per content chunk (a file produces one or many chunks).

| Column | Type | Description |
|---|---|---|
| `chunk_id` | string (UUID) | Primary identifier for this chunk |
| `file_id` | int | Foreign reference to `files.id` in the metadata DB |
| `file_path` | string | Denormalized copy of the file path, for fast source display without a join |
| `chunk_text` | string | The actual chunk content (used for full-text/hybrid search) |
| `chunk_index` | int | Position of this chunk within its file (0-based) |
| `embedding` | vector(float32) | Embedding vector (dimension depends on model — e.g. 768 for nomic-embed-text) |
| `source_type` | string | `text`, `code`, `pdf`, `image` — enables filtered search |
| `indexed_at` | timestamp | When this chunk was created |

Notes:
- `file_path` and `source_type` are intentionally denormalized into LanceDB
  (duplicated from the metadata DB) so retrieval + source display doesn't
  require a cross-database join on every query — a deliberate tradeoff of
  storage duplication for query simplicity/speed.
- LanceDB's native hybrid search operates over `embedding` (vector search)
  and `chunk_text` (full-text search) together.

## 3. Relationship Between the Two Stores

```
files (SQLite)                    chunks (LanceDB)
┌─────────────┐                   ┌──────────────────┐
│ id          │──────────────────▶│ file_id           │
│ path        │                   │ file_path (denorm)│
│ content_hash│                   │ chunk_text         │
│ chunk_count │                   │ embedding          │
│ status      │                   │ chunk_index         │
└─────────────┘                   └──────────────────┘
```

- On file create/modify: extract → chunk → embed → insert N rows into
  `chunks`, then upsert one row into `files` with the new `content_hash` and
  `chunk_count`.
- On file delete: delete all `chunks` rows where `file_id` matches, then
  delete the `files` row.
- On file modify (content changed): delete old `chunks` rows for that
  `file_id` before inserting the new ones, to avoid stale chunks lingering
  alongside fresh ones.

## 4. Data Lifecycle / Retention

- No automatic expiry — an indexed file stays indexed until its source file
  is deleted or moved outside a watched directory.
- `daemon_log` may be pruned periodically (e.g., keep last N days) to avoid
  unbounded growth, since it's operational data, not user-facing content.
- Failed extractions (`status = 'failed'` in `files`) are retained with
  `error_message` so `raga status` can surface them, rather than being
  silently dropped (ties to the Open Question in Requirements about failed
  extraction handling).

## 5. Notes on Redaction (Open Question Carryover)

If secret/API-key redaction (raised as an open question in Requirements) is
implemented, it happens **before** the `chunks` insert — i.e., redaction is
part of the Chunker/Embedder step in the Ingestion Pipeline, not a database
concern. No schema changes are needed to support it; it simply changes what
text ends up in `chunk_text`.
