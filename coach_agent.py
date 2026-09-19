"""도구 호출형 감정 코치 Agent.

의도를 판별해 필요한 도구만 순서대로 실행하고, 도구 이름만 담긴 실행 추적을 반환한다.
(실행 추적에 일기 원문을 넣지 않는다.)

코치 문장은 두 경로 중 하나로 만들어지며 `response_type`으로 구분된다.
  llm_grounded  : 검색된 출처 카드를 컨텍스트로 받은 생성형 AI 문장
  rule_template : 키 미설정·호출 실패·안전 검사 탈락 시 규칙 기반 문장
"""

REST_WORDS = ('추천', '쉬', '휴식', '호흡', '활동', '걷', '도움', '방법')

REFLECTIONS = {
    '불안': '걱정되는 마음이 있군요. 지금 가장 크게 걸리는 생각을 하나씩 이야기해도 좋아요.',
    '슬픔': '마음이 무거운 하루였군요. 그 마음을 서둘러 바꾸지 않아도 괜찮아요.',
    '분노': '답답한 마음이 느껴져요. 어떤 일이 특히 마음에 남았는지 들려주세요.',
    '기쁨': '기분 좋은 순간이 있었군요. 오래 기억하고 싶은 장면이 있나요?',
    '상처': '마음이 다친 듯 느껴지는군요. 무엇이 가장 서운했는지 천천히 이야기해도 좋아요.',
    '당황': '예상하지 못한 일 때문에 놀랐을 수 있어요. 지금 필요한 것을 함께 정리해볼까요?',
}

DISCLAIMER = {
    'llm_grounded': 'AI가 생성한 문장이며 의료적 진단이 아니에요. 검색된 출처 안에서만 답하도록 제한했어요.',
    'rule_template': '감정 분류와 활동 제안은 의료적 진단이 아니며, 코치 문장은 규칙 기반이에요.',
}


def choose_intent(text: str, context: str) -> str:
    if context == 'diary':
        return 'understand_and_rest'
    return 'rest' if any(word in text for word in REST_WORDS) else 'understand'


def _template_message(context, intent, emotion, recommendation):
    message = ('쉬는 방법을 찾고 계시군요.' if context == 'chat' and intent == 'rest'
               else REFLECTIONS.get(emotion, '말해줘서 고마워요. 지금 마음을 조금 더 들려주세요.'))
    if recommendation and recommendation['cards']:
        card = recommendation['cards'][0]
        message += f" 지금은 ‘{card['title']}’ 활동을 천천히 시도해 볼 수 있어요."
    return message


def run_coach_agent(text, stress, context, memory_token, analyze_tool, recommend_tool,
                    known_emotion=None, grounding_tool=None):
    """제한된 순서로 도구를 호출하고, 생성 경로를 공개한 응답을 반환한다."""
    intent = choose_intent(text, context)
    analysis = None
    trace = []

    if context == 'chat' and intent == 'rest':
        # "쉬는 방법 추천해줘" 같은 요청에는 감정 근거가 없다. 추정해 단정하지 않는다.
        emotion = known_emotion or '미상'
    else:
        analysis = analyze_tool(text, stress)
        emotion = analysis['labels'][0]['name']
        trace.append({'tool': 'analyze_emotion', 'status': 'completed'})

    recommendation = None
    if intent in ('understand_and_rest', 'rest'):
        recommendation = recommend_tool(emotion, stress, memory_token)
        trace.append({'tool': 'recommend_healing', 'status': 'completed'})

    grounding = None
    if recommendation and grounding_tool:
        grounding = grounding_tool(emotion, stress)
        trace.append({'tool': 'retrieve_grounding', 'status': 'completed'})

    # 생성형 경로가 성공했을 때만 그 문장을 쓰고, 아니면 규칙 기반으로 되돌린다.
    if grounding and grounding.get('generation') == 'llm_grounded':
        response_type = 'llm_grounded'
        message = grounding['answer']
        trace.append({'tool': 'generate_coach_message', 'status': 'completed',
                      'model': grounding.get('model')})
    else:
        response_type = 'rule_template'
        message = _template_message(context, intent, emotion, recommendation)
        if grounding:
            trace.append({'tool': 'generate_coach_message', 'status': 'fallback',
                          'reason': grounding.get('fallback_reason')})

    return {
        'intent': intent,
        'message': message,
        'response_type': response_type,
        'analysis': analysis,
        'recommendation': recommendation,
        'grounding': grounding,
        'tool_trace': trace,
        'disclaimer': DISCLAIMER[response_type],
    }
