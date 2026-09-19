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
    {
        'id': 'plant-care-10m', 'kind': '꽃·나무', 'title': '초록 식물 돌보기', 'minutes': 10,
        'description': '창가의 식물 잎을 살피고 물이 필요한지 천천히 확인해보세요.',
        'emotions': {'슬픔', '상처', '분노', '당황'},
        'source_title': 'RHS 실내 식물 안내',
        'source_url': 'https://www.rhs.org.uk/houseplants',
    },
    {
        'id': 'copying-10m', 'kind': '필사', 'title': '10분 짧은 필사', 'minutes': 10,
        'description': '마음에 닿는 문장을 한두 줄 골라 천천히 옮겨 적어보세요. 긴 원문은 저장하지 않아요.',
        'emotions': {'불안', '슬픔', '상처', '당황'},
        'source_title': 'Project Gutenberg 공개 도서',
        'source_url': 'https://www.gutenberg.org/',
    },
    {
        'id': 'music-search-10m', 'kind': '음악', 'title': '차분한 음악 찾아보기', 'minutes': 10,
        'description': '자동 재생 없이 원하는 플랫폼에서 ‘차분한 음악’을 직접 골라보세요.',
        'emotions': {'불안', '슬픔', '상처', '분노', '기쁨'},
        'source_title': 'YouTube 검색으로 열기',
        'source_url': 'https://www.youtube.com/results?search_query=%EC%B0%A8%EB%B6%84%ED%95%9C+%EC%9D%8C%EC%95%85',
    },
    {
        'id': 'sketch-10m', 'kind': '취미', 'title': '10분 선 그리기', 'minutes': 10,
        'description': '잘 그리려 하지 말고 종이에 선과 모양을 자유롭게 반복해보세요.',
        'emotions': {'불안', '당황', '분노', '슬픔'},
        'source_title': 'MoMA 미술 활동 자료',
        'source_url': 'https://www.moma.org/magazine/articles/948',
    },
)


def retrieve_activities(emotion: str, stress: int, minutes: int) -> list[dict]:
    available = [item for item in ACTIVITIES if item['minutes'] <= minutes]
    ranked = sorted(available, key=lambda item: (
        emotion in item['emotions'],
        stress >= 4 and item['id'] in {'breathing-1m', 'grounding-5-4-3-2-1'},
        item['kind'] in {'꽃·나무', '필사', '음악', '취미'},
        -item['minutes'],
    ), reverse=True)
    return [{key: value for key, value in item.items() if key != 'emotions'} for item in ranked]
