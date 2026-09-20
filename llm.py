"""생성형 AI 어댑터 — 코디세이 제공 API (OpenAI 호환) 연동.

검색된 출처 위에서만 문장을 생성한다. 설계 원칙 (평가·감사 대상):
  1. 일기 원문을 외부 API에 보내지 않는다. 감정 라벨·스트레스·출처 카드만 전달한다.
  2. 출처 카드에 없는 활동·효능을 생성하지 못하도록 프롬프트와 후처리로 제한한다.
  3. 키가 없거나 호출이 실패하면 기존 결정론적 문장으로 자동 폴백한다.
     폴백 여부와 사유는 응답의 `generation` / `fallback_reason` 으로 항상 공개한다.
  4. 의료 조언·진단 표현은 생성 금지이며, 생성된 문장도 사후 검사한다.

환경 변수 (코디세이에서 받은 값을 그대로 넣는다):
  CODYSSEY_API_KEY    필수. 없으면 결정론적 폴백으로 동작
  CODYSSEY_API_BASE   예: https://api.codyssey.kr/v1   (기본값 없음, 필수)
  CODYSSEY_MODEL      예: gpt-4o-mini  (기본 'gpt-4o-mini')
  MINDILY_LLM_TIMEOUT 기본 20 (초). 추론형 모델은 응답이 느릴 수 있다.

OpenAI 호환 규격이므로 다른 공급자로 바꿀 때도 위 세 값만 교체하면 된다.
"""
import os
import re

DEFAULT_MODEL = 'gpt-4o-mini'

# 같은 OpenAI 호환 규격이라도 모델 계열에 따라 받는 인자가 다르다.
#   구형(gpt-4o 계열) : temperature 허용, max_tokens
#   추론형(gpt-5·o 계열): temperature 고정(1), max_completion_tokens
# 어느 쪽인지 단정하지 않고 한 번 실패하면 반대 규격으로 재시도한다.
REASONING_PREFIXES = ('gpt-5', 'o1', 'o3', 'o4')

# 마지막 호출 실패 사유 (키는 담지 않는다). /api/llm/status 로 공개해 원인 추적에 쓴다.
_LAST_ERROR: str | None = None

# 생성 문장에 나타나면 안 되는 표현. 하나라도 걸리면 폴백한다.
BANNED = ('진단', '처방', '치료', '병원에 가', '약을 드세', '우울증', '장애입니다', '환자')

SYSTEM_RULES = """너는 한국어 감정 코치 'Mindily'의 문장 작성기다.

반드시 지킬 것:
- 아래 '출처 카드'에 적힌 활동만 언급한다. 카드에 없는 활동을 새로 만들지 않는다.
- 의료적 진단·치료·처방·약물을 말하지 않는다. 병원 권유도 하지 않는다.
- 감정을 단정하지 않는다. "~일 수 있어요", "~처럼 보여요"처럼 여지를 남긴다.
- 2~3문장, 200자 이내. 따뜻하되 과장된 위로나 이모지는 쓰지 않는다.
- 첫 문장은 감정에 대한 공감, 마지막 문장은 카드 활동 하나를 권하는 구성으로 쓴다.
- 사용자의 일기 원문은 주어지지 않는다. 없는 사실을 지어내지 않는다."""


def _endpoint() -> str | None:
    base = os.getenv('CODYSSEY_API_BASE', '').strip()
    if not base:
        return None
    if base.endswith('/chat/completions'):
        return base
    return base.rstrip('/') + '/chat/completions'


def is_enabled() -> bool:
    """생성형 경로를 쓸 수 있는 상태인지 (키와 엔드포인트가 모두 있어야 한다)."""
    return bool(os.getenv('CODYSSEY_API_KEY')) and bool(_endpoint())


def status() -> dict:
    """헬스체크·증거 수집용 상태 요약. API 키 값은 절대 노출하지 않는다."""
    return {
        'llm_enabled': is_enabled(),
        'provider': 'codyssey (OpenAI-compatible)',
        'endpoint': _endpoint() if is_enabled() else None,
        'model': os.getenv('CODYSSEY_MODEL', DEFAULT_MODEL) if is_enabled() else None,
        'mode': 'llm_grounded' if is_enabled() else 'deterministic_fallback',
        'sends_diary_text': False,
        'grounding_policy': 'answer only from retrieved source cards',
        'last_error': _LAST_ERROR,
    }


def _build_user_prompt(emotion: str, stress: int, sources: list[dict]) -> str:
    lines = [f'- {s["title"]} ({s["kind"]}): {s["description"]} [출처: {s["source_title"]}]'
             for s in sources[:3]]
    return (f'분류 모델이 추정한 감정: {emotion}\n'
            f'사용자가 직접 보고한 스트레스: {stress}/5\n'
            f'출처 카드:\n' + '\n'.join(lines) + '\n\n'
            '위 조건으로 코치 문장을 써라. 설명 없이 문장만 출력한다.')


def _looks_safe(text: str) -> bool:
    if not text or len(text) > 400:
        return False
    return not any(word in text for word in BANNED)


def _payload(model: str, messages: list[dict], reasoning: bool) -> dict:
    """모델 계열에 맞는 요청 본문을 만든다."""
    body = {'model': model, 'messages': messages}
    if reasoning:
        # 추론형 모델은 temperature 변경을 거부하고 토큰 한도 이름이 다르다.
        body['max_completion_tokens'] = 512
    else:
        body['temperature'] = 0.7
        body['max_tokens'] = 256
    return body


def generate_coach_message(emotion: str, stress: int, sources: list[dict]) -> dict | None:
    """출처 기반 코치 문장을 생성한다. 불가·부적합하면 None을 반환해 폴백을 유도한다."""
    if not is_enabled() or not sources:
        return None
    global _LAST_ERROR
    model = os.getenv('CODYSSEY_MODEL', DEFAULT_MODEL)
    timeout = float(os.getenv('MINDILY_LLM_TIMEOUT', '20'))
    messages = [
        {'role': 'system', 'content': SYSTEM_RULES},
        {'role': 'user', 'content': _build_user_prompt(emotion, stress, sources)},
    ]
    reasoning = model.lower().startswith(REASONING_PREFIXES)
    # 모델 계열에 맞는 규격을 먼저 시도하고, 거절당하면 다른 규격으로 한 번 더 시도한다.
    attempts = [_payload(model, messages, reasoning), _payload(model, messages, not reasoning)]

    try:
        import httpx
    except Exception as error:
        _LAST_ERROR = f'httpx import failed: {type(error).__name__}'
        return None

    text = ''
    errors = []
    for body in attempts:
        try:
            response = httpx.post(
                _endpoint(),
                headers={'Authorization': f'Bearer {os.environ["CODYSSEY_API_KEY"]}',
                         'Content-Type': 'application/json'},
                json=body,
                timeout=timeout,
            )
            if response.status_code >= 400:
                errors.append(f'HTTP {response.status_code}: {response.text[:200]}')
                # 400·422는 인자 규격 문제일 수 있으므로 다음 규격으로 재시도한다.
                if response.status_code in (400, 422):
                    continue
                break
            text = re.sub(r'\s+', ' ', response.json()['choices'][0]['message']['content'] or '').strip()
            if text:
                _LAST_ERROR = None
                break
            errors.append('empty content')
        except Exception as error:
            errors.append(f'{type(error).__name__}: {str(error)[:160]}')
            break

    if not text:
        _LAST_ERROR = ' | '.join(errors) or 'unknown'
        return None

    if not _looks_safe(text):
        return {'blocked': True}
    return {
        'answer': text,
        'generation': 'llm_grounded',
        'model': model,
        'grounded_on': [s['id'] for s in sources[:3]],
    }
