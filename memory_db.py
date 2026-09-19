"""Optional anonymous activity preference memory; no diary text or location."""
import hashlib
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


def database_path() -> Path:
    return Path(os.getenv("MINDILY_MEMORY_DB", Path(__file__).resolve().parent / "data" / "memory.sqlite3"))


def _connect():
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.execute("""CREATE TABLE IF NOT EXISTS memory (
        token_hash TEXT PRIMARY KEY,
        preferred_kind TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""")
    conn.commit()
    return conn


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def remember(token: str, preferred_kind: str) -> None:
    with closing(_connect()) as conn:
        with conn:
            conn.execute("""INSERT INTO memory VALUES (?, ?, ?)
                ON CONFLICT(token_hash) DO UPDATE SET preferred_kind=excluded.preferred_kind,
                updated_at=excluded.updated_at""", (
                    _hash(token), preferred_kind, datetime.now(timezone.utc).isoformat()))


def recall(token: str) -> str | None:
    with closing(_connect()) as conn:
        row = conn.execute("SELECT preferred_kind FROM memory WHERE token_hash=?", (_hash(token),)).fetchone()
        return row[0] if row else None


def forget(token: str) -> bool:
    with closing(_connect()) as conn:
        with conn:
            return bool(conn.execute("DELETE FROM memory WHERE token_hash=?", (_hash(token),)).rowcount)
