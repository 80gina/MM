"""Small, inspectable tool-using coach. Responses are templates, not LLM output."""

REST_WORDS = ('추천', '쉬', '휴식', '호흡', '활동', '걷', '도움', '방법')

REFLECTIONS = {
    '불안': '걱정되는 마음이 있군요. 지금 가장 크게 걸리는 생각을 하나씩 이야기해도 좋아요.',
    '슬픔': '마음이 무거운 하루였군요. 그 마음을 서둘러 바꾸지 않아도 괜찮아요.',
    '분노': '답답한 마음이 느껴져요. 어떤 일이 특히 마음에 남았는지 들려주세요.',
    '기쁨': '기분 좋은 순간이 있었군요. 오래 기억하고 싶은 장면이 있나요?',
    '상처': '마음이 다친 듯 느껴지는군요. 무엇이 가장 서운했는지 천천히 이야기해도 좋아요.',
    '당황': '예상하지 못한 일 때문에 놀랐을 수 있어요. 지금 필요한 것을 함께 정리해볼까요?',
}


def choose_intent(text: str, context: str) -> str:
    if context == 'diary':
        return 'understand_and_rest'
    return 'rest' if any(word in text for word in REST_WORDS) else 'understand'


def run_coach_agent(text, stress, context, memory_token, analyze_tool, recommend_tool, known_emotion=None):
    """Plan a bounded sequence, invoke tools, and return a redacted execution trace."""
    intent = choose_intent(text, context)
    analysis = None
    trace = []
    if context == 'chat' and intent == 'rest':
        # A request such as "쉬는 방법 추천해줘" contains no reliable emotion evidence.
        emotion = known_emotion or '미상'
    else:
        analysis = analyze_tool(text, stress)
        emotion = analysis['labels'][0]['name']
        trace.append({'tool': 'analyze_emotion', 'status': 'completed'})
    recommendation = None
    if intent in ('understand_and_rest', 'rest'):
        recommendation = recommend_tool(emotion, stress, memory_token)
        trace.append({'tool': 'recommend_healing', 'status': 'completed'})

    message = ('쉬는 방법을 찾고 계시군요.' if context == 'chat' and intent == 'rest'
               else REFLECTIONS.get(emotion, '말해줘서 고마워요. 지금 마음을 조금 더 들려주세요.'))
    if recommendation and recommendation['cards']:
        card = recommendation['cards'][0]
        message += f" 지금은 ‘{card['title']}’ 활동을 천천히 시도해 볼 수 있어요."

    return {
        'intent': intent,
        'message': message,
        'response_type': 'rule_template',
        'analysis': analysis,
        'recommendation': recommendation,
        'tool_trace': trace,
        'disclaimer': '감정 분류와 활동 제안은 의료적 진단이 아니며, 코치 문장은 규칙 기반입니다.',
    }
