"""Consent, bounded input, editable draft data, and failure fallback checks."""
from unittest.mock import patch
import json

from fastapi.testclient import TestClient

from server import app


client = TestClient(app)
diary = '오늘 발표를 마친 뒤 친구와 대화했어요. 마음이 긴장됐어요.'

with patch('llm.is_enabled', return_value=False):
    denied = client.post('/api/diary/organizer-draft', json={'text': diary, 'emotion': '불안'})
    assert denied.status_code == 422
    draft = client.post('/api/diary/organizer-draft', json={
        'text': diary, 'emotion': '불안', 'consent': True})
    assert draft.status_code == 200
    assert draft.json()['generation'] == 'extractive_fallback'
    assert '발표' in draft.json()['event']
    assert '불안' in draft.json()['feeling']

    report_denied = client.post('/api/report/events', json={
        'entries': [{'date': '9월 20일', 'text': diary}]})
    assert report_denied.status_code == 422
    report = client.post('/api/report/events', json={
        'entries': [{'date': '9월 20일', 'text': diary}], 'consent': True})
    assert report.status_code == 200
    assert report.json()['generation'] == 'extractive_fallback'
    assert '9월 20일' in report.json()['events']
    assert client.post('/api/report/events', json={
        'entries': [{'date': '9월 20일', 'text': diary}] * 11, 'consent': True}).status_code == 422

with patch('diary_draft._generate_json', return_value={'event': '발표를 했다.', 'feeling': '긴장됐다.'}):
    generated = client.post('/api/diary/organizer-draft', json={
        'text': diary, 'emotion': '불안', 'consent': True})
    assert generated.json()['generation'] == 'llm_draft'
    assert generated.json()['event'] == '발표를 했다.'


class FakeResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {'choices': [{'message': {'content': '{"event":"발표를 했다.","feeling":"긴장됐다."}'}}]}


sent = []
def fake_post(url, **kwargs):
    sent.append({'url': url, 'body': kwargs['json']})
    return FakeResponse()


with patch.dict('os.environ', {'CODYSSEY_API_KEY': 'test-only',
                               'CODYSSEY_API_BASE': 'https://example.invalid/v1'}), \
     patch('diary_draft.httpx.post', side_effect=fake_post):
    no_consent = client.post('/api/diary/organizer-draft', json={'text': diary, 'consent': False})
    assert no_consent.status_code == 422 and not sent
    yes_consent = client.post('/api/diary/organizer-draft', json={
        'text': diary, 'emotion': '불안', 'consent': True})
    assert yes_consent.json()['generation'] == 'llm_draft'
    assert diary in json.dumps(sent[0]['body'], ensure_ascii=False)

print('diary draft and report event consent, generation, fallback: OK')
