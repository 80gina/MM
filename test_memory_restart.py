"""Prove opted-in preference survives separate processes and can be deleted."""
import os
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path


def run_in_new_process(code: str, db_path: Path) -> str:
    env = {**os.environ, 'MINDILY_MEMORY_DB': str(db_path)}
    result = subprocess.run(
        [sys.executable, '-c', code], cwd=Path(__file__).resolve().parent,
        env=env, text=True, capture_output=True, check=True,
    )
    return result.stdout.strip()


with tempfile.TemporaryDirectory() as directory:
    db_path = Path(directory) / 'memory.sqlite3'
    token = 'a' * 64  # Synthetic token; never use a participant's token in tests.

    run_in_new_process(
        f"from memory_db import remember; remember('{token}', '걷기')", db_path)
    assert run_in_new_process(
        f"from memory_db import recall; print(recall('{token}'))", db_path) == '걷기'

    with closing(sqlite3.connect(db_path)) as connection:
        row = connection.execute('SELECT token_hash, preferred_kind FROM memory').fetchone()
    assert row[0] != token and len(row[0]) == 64 and row[1] == '걷기'

    assert run_in_new_process(
        f"from memory_db import forget; print(forget('{token}'))", db_path) == 'True'
    assert run_in_new_process(
        f"from memory_db import recall; print(recall('{token}'))", db_path) == 'None'

    run_in_new_process(
        f"from memory_db import remember; remember('{token}', '호흡')", db_path)
    old_time = (datetime.now(timezone.utc) - timedelta(days=31)).isoformat()
    with closing(sqlite3.connect(db_path)) as connection:
        with connection:
            connection.execute('UPDATE memory SET updated_at=?', (old_time,))
    assert run_in_new_process(
        f"from memory_db import recall; print(recall('{token}'))", db_path) == 'None'
    with closing(sqlite3.connect(db_path)) as connection:
        assert connection.execute('SELECT COUNT(*) FROM memory').fetchone()[0] == 0

print('preference survives restart; hashed token, deletion and 30-day expiry verified: OK')
