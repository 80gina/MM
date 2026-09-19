"""Mindily의 검색 증강 응답 계층.

`retrieve_grounding`이 출처 카드를 고르고, `answer_with_grounding`이 그 위에서만
문장을 만든다. 생성 경로는 두 가지이며 응답의 `generation` 필드로 항상 구분된다.

  llm_grounded           : 출처 카드를 컨텍스트로 받은 생성형 AI 문장
  deterministic_fallback : 키 미설정·호출 실패·안전 검사 탈락 시 규칙 기반 문장

두 경로 모두 동일한 출처 카드를 `sources`로 함께 반환한다. 어느 경로든 사용자는
"왜 이 활동을 권했는가"를 출처 링크로 확인할 수 있다.
"""
from healing_knowledge import retrieve_activities
import llm


def retrieve_grounding(emotion: str, stress: int, minutes: int = 20) -> list[dict]:
    cards = retrieve_activities(emotion, stress, minutes)
    return [{
        'id': card['id'],
        'title': card['title'],
        'kind': card['kind'],
        'description': card['description'],
        'source_title': card['source_title'],
        'source_url': card['source_url'],
    } for card in cards]


def _fallback_answer(sources: list[dict]) -> dict:
    first = sources[0]
    return {
        'answer': f"지금은 ‘{first['title']}’부터 천천히 시도해 볼 수 있어요. {first['description']}",
        'generation': 'deterministic_fallback',
    }


def answer_with_grounding(emotion: str, stress: int, minutes: int = 20) -> dict:
    sources = retrieve_grounding(emotion, stress, minutes)
    if not sources:
        return {
            'answer': '지금 바로 고를 수 있는 출처 있는 활동을 찾지 못했어요.',
            'sources': [], 'generation': 'no_source',
            'llm_enabled': llm.is_enabled(),
        }

    generated = llm.generate_coach_message(emotion, stress, sources)
    if generated and not generated.get('blocked'):
        result = generated
        fallback_reason = None
    else:
        result = _fallback_answer(sources)
        fallback_reason = ('safety_filter' if generated and generated.get('blocked')
                           else ('not_configured' if not llm.is_enabled() else 'call_failed'))

    return {
        **result,
        'sources': sources[:3],
        'grounding_policy': 'answer only from retrieved source cards',
        'llm_enabled': llm.is_enabled(),
        'fallback_reason': fallback_reason,
        'sends_diary_text': False,
    }
