"""Small, source-backed activity catalog for retrieval-based recommendations."""

ACTIVITIES = (
    {
        'id': 'breathing-1m', 'kind': '호흡', 'title': '1분 호흡하기', 'minutes': 1,
        'description': '편안한 자세에서 무리하지 않고 천천히 숨을 들이쉬고 내쉬어 보세요.',
        'emotions': {'불안', '당황', '분노', '상처', '슬픔', '기쁨'},
        'steps': ['편한 자세로 앉아 어깨의 힘을 뺍니다.', '코로 4초간 천천히 들이쉽니다.', '2초 멈췄다가 입으로 6초간 길게 내쉽니다.', '무리하지 말고 다섯 번만 반복합니다.', '어지러우면 바로 멈추고 평소대로 숨 쉽니다.'],
        'source_title': 'NHS 호흡 연습',
        'source_url': 'https://www.nhs.uk/mental-health/self-help/guides-tools-and-activities/breathing-exercises-for-stress/',
    },
    {
        'id': 'grounding-5-4-3-2-1', 'kind': '감각활동', 'title': '주변 감각 돌아보기', 'minutes': 5,
        'description': '보이는 것 다섯 가지부터 천천히 세며 지금 있는 곳에 주의를 돌려보세요.',
        'emotions': {'불안', '당황', '분노'},
        'steps': ['지금 눈에 보이는 것 다섯 가지를 천천히 셉니다.', '귀에 들리는 소리 네 가지를 찾습니다.', '손끝에 닿는 감촉 세 가지를 느껴봅니다.', '맡을 수 있는 냄새 두 가지를 떠올립니다.', '마지막으로 입안의 맛 한 가지에 주의를 둡니다.'],
        'source_title': 'Kent Community Health NHS 감각 활동',
        'source_url': 'https://www.kentcht.nhs.uk/leaflet/panic-attacks/',
    },
    {
        'id': 'walk-10m', 'kind': '걷기', 'title': '가볍게 걸어보기', 'minutes': 10,
        'description': '가능한 환경이라면 몸 상태에 맞춰 가까운 곳을 천천히 걸어보세요.',
        'emotions': {'기쁨', '슬픔', '상처', '분노'},
        'steps': ['신발을 신고 문밖으로 한 걸음 나갑니다.', '목적지를 정하지 않고 걷습니다.', '발바닥이 땅에 닿는 느낌에만 주의를 둡니다.', '숨이 차면 속도를 줄입니다.', '돌아와서 물을 한 잔 마십니다.'],
        'source_title': 'WHO 신체 활동 자료',
        'source_url': 'https://www.who.int/news-room/fact-sheets/detail/physical-activity',
    },
    {
        'id': 'plant-care-10m', 'kind': '꽃·나무', 'title': '초록 식물 돌보기', 'minutes': 10,
        'description': '창가의 식물 잎을 살피고 물이 필요한지 천천히 확인해보세요.',
        'emotions': {'슬픔', '상처', '분노', '당황'},
        'steps': ['가까운 화분이나 창밖 나무를 찾습니다.', '잎의 앞뒤를 천천히 살펴봅니다.', '흙에 손가락을 2cm 넣어 마른지 확인합니다.', '말랐으면 물을 천천히 줍니다.', '잎에 앉은 먼지를 한 장씩 닦아냅니다.'],
        'source_title': 'RHS 실내 식물 안내',
        'source_url': 'https://www.rhs.org.uk/houseplants',
    },
    {
        'id': 'copying-10m', 'kind': '필사', 'title': '10분 짧은 필사', 'minutes': 10,
        'description': '마음에 닿는 문장을 한두 줄 골라 천천히 옮겨 적어보세요. 긴 원문은 저장하지 않아요.',
        'emotions': {'불안', '슬픔', '상처', '당황'},
        'steps': ['종이와 펜을 준비합니다.', '위에 나온 인용구를 한 글자씩 옮겨 적습니다.', '글씨를 잘 쓰려 하지 않습니다.', '다 적었으면 소리 내어 한 번 읽습니다.', '마음에 남는 단어에 동그라미를 칩니다.'],
        'source_title': 'Project Gutenberg 공개 도서',
        'source_url': 'https://www.gutenberg.org/',
    },
    {
        'id': 'music-search-10m', 'kind': '음악', 'title': '차분한 음악 찾아보기', 'minutes': 10,
        'description': '자동 재생 없이 원하는 플랫폼에서 ‘차분한 음악’을 직접 골라보세요.',
        'emotions': {'불안', '슬픔', '상처', '분노', '기쁨'},
        'steps': ['듣고 싶은 분위기를 한 단어로 정합니다.', '평소 쓰는 음악 앱에서 직접 검색합니다.', '자동 재생은 끄고 한 곡만 고릅니다.', '눈을 감고 처음 30초만 들어봅니다.', '계속 듣고 싶으면 그대로 두세요.'],
        'source_title': 'YouTube 검색으로 열기',
        'source_url': 'https://www.youtube.com/results?search_query=%EC%B0%A8%EB%B6%84%ED%95%9C+%EC%9D%8C%EC%95%85',
    },
    {
        'id': 'sketch-10m', 'kind': '취미', 'title': '10분 선 그리기', 'minutes': 10,
        'description': '잘 그리려 하지 말고 종이에 선과 모양을 자유롭게 반복해보세요.',
        'emotions': {'불안', '당황', '분노', '슬픔'},
        'steps': ['종이 한 장과 펜을 꺼냅니다.', '선을 위아래로 천천히 반복해 긋습니다.', '손이 가는 대로 원과 네모를 채웁니다.', '잘 그리려는 마음이 들면 손을 더 느리게 합니다.', '10분이 되면 그대로 덮어둡니다.'],
        'source_title': 'MoMA 미술 활동 자료',
        'source_url': 'https://www.moma.org/magazine/articles/948',
    },
    {
        'id': 'sound-rain', 'kind': '자연의 소리', 'title': '빗소리 듣기', 'minutes': 5,
        'description': '창밖에 비가 내리는 듯한 소리를 앱 안에서 바로 들을 수 있어요.',
        'emotions': {'불안', '슬픔', '상처', '당황'},
        'sound': 'rain',
        'steps': ['아래 재생 버튼을 누릅니다.', '소리가 너무 크면 기기 음량을 줄입니다.',
                  '눈을 감고 빗줄기가 굵어졌다 가늘어지는 흐름을 따라갑니다.',
                  '생각이 떠오르면 밀어내지 말고 소리로 다시 돌아옵니다.',
                  '충분해지면 정지 버튼을 누릅니다.'],
        'source_title': '브라우저에서 직접 만든 소리 (녹음 파일 아님)',
        'source_url': 'https://developer.mozilla.org/ko/docs/Web/API/Web_Audio_API',
    },
    {
        'id': 'sound-wind', 'kind': '자연의 소리', 'title': '바람 소리 듣기', 'minutes': 5,
        'description': '나뭇가지 사이를 지나는 바람처럼 느리게 오르내리는 소리예요.',
        'emotions': {'불안', '분노', '당황', '기쁨'},
        'sound': 'wind',
        'steps': ['아래 재생 버튼을 누릅니다.', '숨을 바람의 속도에 맞춰 천천히 쉽니다.',
                  '소리가 커질 때 들이쉬고 잦아들 때 내쉽니다.',
                  '억지로 맞추지 말고 편한 만큼만 따라갑니다.',
                  '충분해지면 정지 버튼을 누릅니다.'],
        'source_title': '브라우저에서 직접 만든 소리 (녹음 파일 아님)',
        'source_url': 'https://developer.mozilla.org/ko/docs/Web/API/Web_Audio_API',
    },
    {
        'id': 'sound-waves', 'kind': '자연의 소리', 'title': '파도 소리 듣기', 'minutes': 5,
        'description': '밀려왔다 물러가는 파도처럼 천천히 반복되는 소리예요.',
        'emotions': {'슬픔', '상처', '불안', '기쁨'},
        'sound': 'waves',
        'steps': ['아래 재생 버튼을 누릅니다.', '파도가 밀려오는 구간을 한 번 세어봅니다.',
                  '열 번을 세는 동안 다른 생각은 잠시 내려둡니다.',
                  '숫자를 놓쳐도 괜찮습니다. 다시 하나부터 셉니다.',
                  '충분해지면 정지 버튼을 누릅니다.'],
        'source_title': '브라우저에서 직접 만든 소리 (녹음 파일 아님)',
        'source_url': 'https://developer.mozilla.org/ko/docs/Web/API/Web_Audio_API',
    },
)


def retrieve_activities(emotion: str, stress: int, minutes: int) -> list[dict]:
    available = [item for item in ACTIVITIES if item['minutes'] <= minutes]
    calming = {'호흡', '감각활동', '자연의 소리'}
    ranked = sorted(available, key=lambda item: (
        emotion in item['emotions'],          # 감정에 맞는 활동을 먼저
        stress >= 4 and item['kind'] in calming,  # 스트레스가 높으면 진정 활동을 먼저
        item['minutes'] <= 5,                 # 짧아서 지금 바로 할 수 있는 것
        -item['minutes'],
    ), reverse=True)
    return [{key: value for key, value in item.items() if key != 'emotions'} for item in ranked]
