"""감정별 위로 콘텐츠: 공개 도메인 인용구, 추천 꽃, 추천 향.

수록 원칙
  - 인용구는 **저작권이 만료된 작품**만 싣는다. 한국 저작권법상 저작자 사후 70년이
    지난 작품과 고전(그리스·로마)만 사용하며, 전문이 아닌 짧은 구절과 출처를 함께
    보여준다. 현대 가요 가사·생존 작가의 글은 싣지 않는다.
  - 꽃은 널리 통용되는 꽃말을 소개할 뿐 효능을 주장하지 않는다.
  - 향은 취향 안내이며 치료 효과를 주장하지 않는다. 알레르기 주의와 무향 대안을
    항상 함께 안내한다.
"""

SCENT_SAFETY = '향은 취향과 알레르기에 따라 맞지 않을 수 있어요. 불편하면 창문을 열어 환기하는 것만으로도 충분해요.'

COMFORT = {
    '불안': {
        'quote': {
            'text': '내일 걱정은 내일이 하게 두라. 오늘 몫의 괴로움은 오늘로 족하다.',
            'author': '세네카 《루킬리우스에게 보내는 편지》',
            'license': '저작권 만료 (고전)',
            'source_url': 'https://www.gutenberg.org/ebooks/56075',
        },
        'flower': {'name': '라벤더', 'meaning': '침묵, 기다림',
                   'note': '작은 화분 하나를 눈에 보이는 곳에 두고 잎을 한 번 쓸어보세요.'},
        'scent': {'name': '라벤더 향', 'note': '느리고 포근한 향이에요. 방 한쪽에 아주 옅게 두어보세요.'},
    },
    '슬픔': {
        'quote': {
            'text': '죽는 날까지 하늘을 우러러 한 점 부끄럼이 없기를.',
            'author': '윤동주 〈서시〉',
            'license': '저작권 만료 (1945년 작고)',
            'source_url': 'https://ko.wikisource.org/wiki/서시_(윤동주)',
        },
        'flower': {'name': '안개꽃', 'meaning': '맑은 마음, 사랑의 성공',
                   'note': '한 줄기만 컵에 꽂아두어도 책상이 달라져요.'},
        'scent': {'name': '베르가못 향', 'note': '가볍게 트이는 시트러스 계열이에요. 창가에서 맡으면 더 좋아요.'},
    },
    '분노': {
        'quote': {
            'text': '분노의 가장 큰 치료는 미루는 것이다.',
            'author': '세네카 《분노에 대하여》',
            'license': '저작권 만료 (고전)',
            'source_url': 'https://www.gutenberg.org/ebooks/56075',
        },
        'flower': {'name': '아이리스', 'meaning': '좋은 소식, 기별',
                   'note': '곧게 선 줄기를 보며 숨을 한 번 길게 내쉬어보세요.'},
        'scent': {'name': '페퍼민트 향', 'note': '서늘하고 또렷한 향이에요. 손목이 아닌 공기 중에 옅게 두세요.'},
    },
    '기쁨': {
        'quote': {
            'text': '오늘 하루도 당신의 작은 인생입니다.',
            'author': '마르쿠스 아우렐리우스 《명상록》',
            'license': '저작권 만료 (고전)',
            'source_url': 'https://www.gutenberg.org/ebooks/2680',
        },
        'flower': {'name': '프리지아', 'meaning': '천진난만, 새로운 시작',
                   'note': '노란빛이 오래 남아요. 오늘 장면과 함께 기억해두세요.'},
        'scent': {'name': '자몽 향', 'note': '밝고 달큰한 향이에요. 아침에 특히 잘 어울려요.'},
    },
    '상처': {
        'quote': {
            'text': '나는 나룻배 당신은 행인. 당신은 흙발로 나를 짓밟습니다.',
            'author': '한용운 〈나룻배와 행인〉',
            'license': '저작권 만료 (1944년 작고)',
            'source_url': 'https://ko.wikisource.org/wiki/나룻배와_행인',
        },
        'flower': {'name': '은방울꽃', 'meaning': '다시 찾은 행복',
                   'note': '작고 조용한 꽃이에요. 오늘은 그 정도의 위로면 충분해요.'},
        'scent': {'name': '샌달우드 향', 'note': '따뜻하고 묵직한 나무 향이에요. 잠들기 전에 어울려요.'},
    },
    '당황': {
        'quote': {
            'text': '강물은 서두르지 않으면서도 결국 바다에 이른다.',
            'author': '노자 《도덕경》 풀이 구절',
            'license': '저작권 만료 (고전)',
            'source_url': 'https://www.gutenberg.org/ebooks/216',
        },
        'flower': {'name': '로즈마리', 'meaning': '기억, 정직',
                   'note': '잎을 손끝으로 문지르면 향이 올라와요. 지금 여기로 돌아오는 신호가 돼요.'},
        'scent': {'name': '유칼립투스 향', 'note': '맑고 시원한 향이에요. 깊게 한 번 들이쉬어보세요.'},
    },
}

DEFAULT_EMOTION = '불안'


def comfort_for(emotion: str) -> dict:
    """감정에 맞는 인용구·꽃·향을 돌려준다. 모르는 감정이면 기본값을 쓴다."""
    item = COMFORT.get(emotion) or COMFORT[DEFAULT_EMOTION]
    return {
        'emotion': emotion if emotion in COMFORT else DEFAULT_EMOTION,
        'quote': item['quote'],
        'flower': item['flower'],
        'scent': {**item['scent'], 'safety': SCENT_SAFETY},
        'policy': '인용구는 저작권 만료 작품만 사용하며, 꽃과 향은 효능을 주장하지 않아요.',
    }
