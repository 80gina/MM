"""Verify source retrieval and opt-in preference deletion without loading KcELECTRA."""
import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient
from server import app


with tempfile.TemporaryDirectory() as directory:
    os.environ['MINDILY_MEMORY_DB'] = str(Path(directory) / 'memory.sqlite3')
    client = TestClient(app)
    payload = {'emotion': '불안', 'stress': 4, 'minutes': 20}
    response = client.post('/api/healing/recommend', json=payload)
    assert response.status_code == 200
    cards = response.json()['cards']
    assert cards and all(card['source_url'].startswith('https://') for card in cards)
    assert response.json()['personalized'] is False
    token = 'a' * 64
    declined = client.post('/api/memory', json={
        'token': token, 'preferred_kind': '걷기', 'consent': False})
    assert declined.status_code == 422
    saved = client.post('/api/memory', json={
        'token': token, 'preferred_kind': '걷기', 'consent': True})
    assert saved.status_code == 200 and saved.json()['saved']
    assert client.post('/api/memory/read', json={'token': token}).json()['preferred_kind'] == '걷기'
    tailored = client.post('/api/healing/recommend', json={**payload, 'memory_token': token}).json()
    assert tailored['personalized'] and tailored['cards'][0]['kind'] == '걷기'
    assert client.post('/api/memory/delete', json={'token': token}).json()['deleted']
    assert client.post('/api/memory/read', json={'token': token}).json()['preferred_kind'] is None

print('retrieval, consent and memory deletion: OK')
