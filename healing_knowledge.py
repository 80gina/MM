"""Small, source-backed activity catalog for retrieval-based recommendations."""

ACTIVITIES = (
    {
        'id': 'breathing-1m', 'kind': '호흡', 'title': '1분 호흡하기', 'minutes': 1,
        'description': '편안한 자세에서 무리하지 않고 천천히 숨을 들이쉬고 내쉬어 보세요.',
        'emotions': {'불안', '당황', '분노', '상처', '슬픔', '기쁨'},
        'source_title': 'NHS 호흡 연습',
        'source_url': 'https://www.nhs.uk/mental-health/self-help/guides-tools-and-activities/breathing-exercises-for-stress/',
    },
    {
        'id': 'grounding-5-4-3-2-1', 'kind': '감각활동', 'title': '주변 감각 돌아보기', 'minutes': 5,
        'description': '보이는 것 다섯 가지부터 천천히 세며 지금 있는 곳에 주의를 돌려보세요.',
        'emotions': {'불안', '당황', '분노'},
        'source_title': 'Kent Community Health NHS 감각 활동',
        'source_url': 'https://www.kentcht.nhs.uk/leaflet/panic-attacks/',
    },
    {
        'id': 'walk-10m', 'kind': '걷기', 'title': '가볍게 걸어보기', 'minutes': 10,
        'description': '가능한 환경이라면 몸 상태에 맞춰 가까운 곳을 천천히 걸어보세요.',
        'emotions': {'기쁨', '슬픔', '상처', '분노'},
        'source_title': 'WHO 신체 활동 자료',
        'source_url': 'https://www.who.int/news-room/fact-sheets/detail/physical-activity',
    },
)


def retrieve_activities(emotion: str, stress: int, minutes: int) -> list[dict]:
    available = [item for item in ACTIVITIES if item['minutes'] <= minutes]
    ranked = sorted(available, key=lambda item: (
        emotion in item['emotions'],
        stress >= 4 and item['id'] in {'breathing-1m', 'grounding-5-4-3-2-1'},
        -item['minutes'],
    ), reverse=True)
    return [{key: value for key, value in item.items() if key != 'emotions'} for item in ranked]
