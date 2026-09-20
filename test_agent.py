"""Check intent routing, tool order, source grounding, and privacy of the trace."""
from fastapi.testclient import TestClient
from unittest.mock import patch

from coach_agent import run_coach_agent
from server import app


calls = []


def analyze(text, stress):
    calls.append('analyze_emotion')
    return {'labels': [{'name': '불안', 'score': 0.8}], 'self_reported_stress': stress}


def recommend(emotion, stress, token):
    calls.append('recommend_healing')
    assert emotion in {'불안', '미상'} and stress == 4 and token is None
    return {'cards': [{'title': '1분 호흡하기', 'source_url': 'https://www.nhs.uk/example'}]}


diary_text = '내일 발표가 걱정돼요.'
result = run_coach_agent(diary_text, 4, 'diary', None, analyze, recommend)
assert calls == ['analyze_emotion', 'recommend_healing']
assert [step['tool'] for step in result['tool_trace']] == calls
assert diary_text not in str(result['tool_trace'])
assert result['recommendation']['cards'][0]['source_url'].startswith('https://')
assert result['response_type'] == 'rule_template'

calls.clear()
reflection = run_coach_agent(diary_text, 4, 'chat', None, analyze, recommend)
assert calls == ['analyze_emotion'] and reflection['recommendation'] is None

calls.clear()
rest = run_coach_agent('쉬는 방법 추천해줘', 4, 'chat', None, analyze, recommend)
assert calls == ['recommend_healing'] and rest['intent'] == 'rest'
assert rest['analysis'] is None and rest['message'].startswith('쉬는 방법을 찾고 계시군요.')

calls.clear()
rest_with_diary = run_coach_agent('호흡 추천해줘', 4, 'chat', None, analyze, recommend, '불안')
assert calls == ['recommend_healing'] and rest_with_diary['recommendation']

client = TestClient(app)
with patch('server.analyze', return_value=analyze(diary_text, 4)), \
     patch('server.recommend_healing', return_value=recommend('불안', 4, None)):
    response = client.post('/api/agent/coach', json={
        'text': diary_text, 'self_reported_stress': 4, 'context': 'diary'})
    assert response.status_code == 200, response.text
    body = response.json()
    assert [step['tool'] for step in body['tool_trace'][:3]] == [
        'analyze_emotion', 'recommend_healing', 'retrieve_grounding']
    assert body['tool_trace'][-1]['tool'] == 'generate_coach_message'
    assert body['grounding']['sources']
    assert client.post('/api/agent/coach', json={
        'text': diary_text, 'self_reported_stress': 6, 'context': 'diary'}).status_code == 422

print('coach agent routing, tool sequence, source, privacy, and validation: OK')
