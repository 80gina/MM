"""생성형 경로와 폴백 동작 검증 (코디세이 OpenAI 호환 API).

CODYSSEY_API_KEY / CODYSSEY_API_BASE 없이도 통과해야 한다.
값이 설정되어 있으면 실제 생성 경로까지 추가로 확인한다.
"""
import os
import json

import llm
from rag import answer_with_grounding

RESULTS = {'checks': []}


def record(name, passed, detail):
    RESULTS['checks'].append({'check': name, 'passed': bool(passed), 'detail': detail})
    assert passed, f'{name}: {detail}'


def test_status_never_leaks_key():
    """상태 응답에 키 이름도, 키 값도 담기지 않는다."""
    dumped = json.dumps(llm.status(), ensure_ascii=False)
    key_value = os.getenv('CODYSSEY_API_KEY')
    leaked = 'CODYSSEY_API_KEY' in dumped or (bool(key_value) and key_value in dumped)
    record('status_no_key_leak', not leaked, dumped)


def test_never_sends_diary_text():
    """일기 원문은 프롬프트에 들어가지 않는다."""
    sources = [{'id': 'breathing-1m', 'kind': '호흡', 'title': '1분 호흡하기',
                'description': '천천히 숨을 쉬어보세요.', 'source_title': 'NHS',
                'source_url': 'https://www.nhs.uk/'}]
    prompt = llm._build_user_prompt('불안', 3, sources)
    secret = '내일 발표를 잘할 수 있을지 걱정돼요.'
    record('prompt_excludes_diary_text', secret not in prompt, '프롬프트에 원문 미포함')
    record('prompt_includes_sources', '1분 호흡하기' in prompt and 'NHS' in prompt, '출처 카드 포함')


def test_fallback_without_key(monkeypatch=None):
    """키가 없으면 결정론적 문장으로 폴백하고 그 사실을 공개한다."""
    saved = os.environ.pop('CODYSSEY_API_KEY', None)
    try:
        result = answer_with_grounding('불안', 3)
        record('fallback_generation_flag',
               result['generation'] == 'deterministic_fallback', result['generation'])
        record('fallback_reason_disclosed',
               result['fallback_reason'] == 'not_configured', result['fallback_reason'])
        record('fallback_keeps_sources', len(result['sources']) > 0, len(result['sources']))
    finally:
        if saved:
            os.environ['CODYSSEY_API_KEY'] = saved


def test_safety_filter_blocks_medical_text():
    record('safety_blocks_diagnosis', not llm._looks_safe('당신은 우울증 진단이 필요합니다.'), 'blocked')
    record('safety_allows_normal', llm._looks_safe('마음이 무거우셨겠어요. 1분 호흡하기부터 해보실래요?'), 'allowed')


def test_live_generation_if_configured():
    """키가 설정된 환경에서만 실제 생성 경로를 확인한다."""
    if not llm.is_enabled():
        RESULTS['checks'].append({'check': 'live_generation', 'passed': None,
                                  'detail': 'CODYSSEY_API_KEY / CODYSSEY_API_BASE 미설정 — 건너뜀'})
        return
    result = answer_with_grounding('불안', 3)
    record('live_generation', result['generation'] == 'llm_grounded', result['generation'])
    record('live_answer_length', 0 < len(result['answer']) <= 400, len(result['answer']))
    record('live_sources_attached', len(result['sources']) > 0, len(result['sources']))


if __name__ == '__main__':
    for fn in (test_status_never_leaks_key, test_never_sends_diary_text,
               test_fallback_without_key, test_safety_filter_blocks_medical_text,
               test_live_generation_if_configured):
        fn()
    RESULTS['llm_enabled'] = llm.is_enabled()
    RESULTS['status'] = llm.status()
    print(json.dumps(RESULTS, ensure_ascii=False, indent=2))
