"""SQLite-backed memory store with FTS5 and vector search."""

import os
import sqlite3
import uuid
from datetime import datetime, timezone

from .embeddings import embed, cosine_similarity

DB_PATH = os.path.join(os.environ.get("BRAIN_DATA_DIR", "data"), "brain.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT DEFAULT '',
    embedding BLOB,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    source TEXT DEFAULT 'manual'
);

CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
    body, tags, category, content='memories', content_rowid='rowid'
);

CREATE TABLE IF NOT EXISTS profile (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

# FTS sync triggers — 'body' maps to memories.content
FTS_TRIGGERS = """
CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
    INSERT INTO memories_fts(rowid, body, tags, category)
    VALUES (new.rowid, new.content, new.tags, new.category);
END;

CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, body, tags, category)
    VALUES ('delete', old.rowid, old.content, old.tags, old.category);
END;

CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, body, tags, category)
    VALUES ('delete', old.rowid, old.content, old.tags, old.category);
    INSERT INTO memories_fts(rowid, body, tags, category)
    VALUES (new.rowid, new.content, new.tags, new.category);
END;
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MemoryStore:
    def __init__(self, db_path: str = DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        self._migrate_fts()
        self.db.executescript(SCHEMA)
        self.db.executescript(FTS_TRIGGERS)

    def _migrate_fts(self):
        """Rebuild FTS table if it has the old broken schema (column named 'content')."""
        row = self.db.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='memories_fts'"
        ).fetchone()
        if row and "body" not in row[0]:
            self.db.executescript("""
                DROP TRIGGER IF EXISTS memories_ai;
                DROP TRIGGER IF EXISTS memories_ad;
                DROP TRIGGER IF EXISTS memories_au;
                DROP TABLE IF EXISTS memories_fts;
            """)
            self.db.executescript(SCHEMA)
            self.db.executescript(FTS_TRIGGERS)
            # Backfill FTS from existing memories
            rows = self.db.execute("SELECT rowid, content, tags, category FROM memories").fetchall()
            for r in rows:
                self.db.execute(
                    "INSERT INTO memories_fts(rowid, body, tags, category) VALUES (?, ?, ?, ?)",
                    (r[0], r[1], r[2], r[3]),
                )
            self.db.commit()

    def remember(self, category: str, content: str, tags: str = "", source: str = "manual") -> dict:
        mid = str(uuid.uuid4())[:8]
        now = _now()
        embedding = embed(content)
        self.db.execute(
            "INSERT INTO memories (id, category, content, tags, embedding, created_at, updated_at, source) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (mid, category, content, tags, embedding, now, now, source),
        )
        self.db.commit()
        return {"id": mid, "category": category, "status": "remembered"}

    def recall(self, query: str, category: str | None = None, limit: int = 5) -> list[dict]:
        query_emb = embed(query)
        rows = self.db.execute("SELECT id, category, content, tags, embedding, created_at FROM memories").fetchall()

        scored = []
        for r in rows:
            if category and r["category"] != category:
                continue
            sim = cosine_similarity(query_emb, r["embedding"])
            scored.append({
                "id": r["id"],
                "category": r["category"],
                "content": r["content"],
                "tags": r["tags"],
                "similarity": round(sim, 4),
                "created_at": r["created_at"],
            })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:limit]

    def forget(self, memory_id: str) -> dict:
        cur = self.db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        self.db.commit()
        if cur.rowcount:
            return {"id": memory_id, "status": "forgotten"}
        return {"id": memory_id, "status": "not found"}

    def list_memories(self, category: str | None = None, tag: str | None = None, limit: int = 20) -> list[dict]:
        if tag:
            rows = self.db.execute(
                "SELECT id, category, content, tags, created_at FROM memories WHERE tags LIKE ? ORDER BY created_at DESC LIMIT ?",
                (f"%{tag}%", limit),
            ).fetchall()
        elif category:
            rows = self.db.execute(
                "SELECT id, category, content, tags, created_at FROM memories WHERE category = ? ORDER BY created_at DESC LIMIT ?",
                (category, limit),
            ).fetchall()
        else:
            rows = self.db.execute(
                "SELECT id, category, content, tags, created_at FROM memories ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def set_profile(self, key: str, value: str) -> dict:
        now = _now()
        self.db.execute(
            "INSERT INTO profile (key, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
            (key, value, now),
        )
        self.db.commit()
        return {"key": key, "status": "saved"}

    def get_profile(self, key: str | None = None) -> dict:
        if key:
            row = self.db.execute("SELECT key, value FROM profile WHERE key = ?", (key,)).fetchone()
            return dict(row) if row else {"key": key, "value": None}
        rows = self.db.execute("SELECT key, value FROM profile").fetchall()
        return {r["key"]: r["value"] for r in rows}

    def context(self, project: str) -> list[dict]:
        """Return all memories related to a project."""
        return self.recall(project, category="projects", limit=10) + \
               self.recall(project, limit=5)
