"""Small retrieval-grounded response layer for Mindily.

The current deployment deliberately uses a deterministic fallback. It returns the
retrieved source context and never pretends that a local classifier generated text.
An external LLM adapter can consume the same context later with explicit review.
"""
from healing_knowledge import retrieve_activities


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


def answer_with_grounding(emotion: str, stress: int, minutes: int = 20) -> dict:
    sources = retrieve_grounding(emotion, stress, minutes)
    if not sources:
        return {
            'answer': '지금 바로 고를 수 있는 출처 있는 활동을 찾지 못했어요.',
            'sources': [], 'generation': 'deterministic_fallback',
        }
    first = sources[0]
    answer = f"지금은 ‘{first['title']}’부터 천천히 시도해 볼 수 있어요. {first['description']}"
    return {
        'answer': answer,
        'sources': sources[:3],
        'generation': 'deterministic_fallback',
        'grounding_policy': 'answer only from retrieved source cards',
        'llm_adapter': 'not_configured',
    }
