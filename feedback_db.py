"""Persist consented, anonymous feedback separately from diary text."""
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def database_path() -> Path:
    return Path(os.getenv("MINDILY_FEEDBACK_DB", Path(__file__).resolve().parent / "data" / "feedback.sqlite3"))


def save_feedback(card_id: str, helpful: bool, satisfaction: int | None, comment: str | None) -> str:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    receipt = uuid4().hex
    with closing(sqlite3.connect(path, timeout=10)) as conn:
        with conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY,
                card_id TEXT NOT NULL,
                helpful INTEGER NOT NULL,
                satisfaction INTEGER,
                comment TEXT,
                created_at TEXT NOT NULL
            )""")
            conn.execute("INSERT INTO feedback VALUES (?, ?, ?, ?, ?, ?)", (
                receipt, card_id, int(helpful), satisfaction, comment,
                datetime.now(timezone.utc).isoformat(),
            ))
    return receipt
