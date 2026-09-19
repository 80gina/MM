"""Exercise feedback validation and disk persistence without loading the model."""
import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

from fastapi.testclient import TestClient
from server import app


with tempfile.TemporaryDirectory() as directory:
    db_path = Path(directory) / "feedback.sqlite3"
    os.environ["MINDILY_FEEDBACK_DB"] = str(db_path)
    client = TestClient(app)
    payload = {"card_id": "session-exit", "satisfaction": 4,
               "comment": "화면을 이해하기 쉬웠어요.", "consent": True}
    response = client.post("/api/feedback", json=payload)
    assert response.status_code == 200
    assert response.json()["saved"] is True
    assert response.json()["receipt"]
    assert db_path.exists()
    with closing(sqlite3.connect(db_path)) as connection:
        rows = connection.execute(
            "SELECT card_id, satisfaction, helpful, comment FROM feedback"
        ).fetchall()
    assert rows == [("session-exit", 4, 1, "화면을 이해하기 쉬웠어요.")]
    declined = client.post("/api/feedback", json={**payload, "consent": False})
    assert declined.status_code == 200 and declined.json()["saved"] is False
    invalid = client.post("/api/feedback", json={**payload, "satisfaction": 6})
    assert invalid.status_code == 422
    missing_rating = client.post("/api/feedback", json={"card_id": "session-exit", "consent": True})
    assert missing_rating.status_code == 422
    with closing(sqlite3.connect(db_path)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM feedback").fetchone()[0] == 1

print("feedback persistence and validation: OK")
