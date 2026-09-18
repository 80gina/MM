"""Mindily: 실제 감정 분류 API와 동일 출처의 UI 제공."""
import os
from pathlib import Path
from contextlib import asynccontextmanager
from threading import Lock

ROOT = Path(__file__).resolve().parent
os.environ.setdefault('HF_HOME', str(ROOT / 'models' / 'cache'))
os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY', '1')
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from uuid import uuid4

MODEL = 'GGARA02/kcelectra-korean-emotion'
REVISION = '2eaf89d8d2cbfd902b93e5ec989db2ec103806fb'
inference_lock = Lock()
feedback_store = []


@asynccontextmanager
async def lifespan(app):
    offline = os.getenv('MINDILY_OFFLINE') == '1'
    app.state.tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION, local_files_only=offline)
    app.state.model = AutoModelForSequenceClassification.from_pretrained(
        MODEL, revision=REVISION, local_files_only=offline, use_safetensors=True
    ).eval()
    yield


app = FastAPI(lifespan=lifespan)


class Diary(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    self_reported_stress: int = Field(ge=1, le=5, strict=True)

    @field_validator('text')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('일기를 입력해주세요.')
        return value.strip()


class HealingRequest(BaseModel):
    emotion: str = Field(min_length=1, max_length=30)
    stress: int = Field(ge=1, le=5, strict=True)
    minutes: int = Field(default=5, ge=1, le=120, strict=True)
    allow_location: bool = False


class Feedback(BaseModel):
    card_id: str = Field(min_length=1, max_length=80)
    helpful: bool
    comment: Optional[str] = Field(default=None, max_length=300)
    consent: bool = False


@app.get('/api/health')
def health():
    return {'status': 'ready', 'model': MODEL, 'revision': REVISION}


@app.post('/api/emotions/analyze')
def analyze(diary: Diary):
    if not inference_lock.acquire(blocking=False):
        raise HTTPException(503, '다른 분석을 진행 중이에요. 잠시 후 다시 시도해주세요.')
    try:
        tokenizer = app.state.tokenizer
        # 모든 입력을 읽되, 학습 길이에 맞춰 128토큰 단위로 분할한다.
        encoded = tokenizer(diary.text, truncation=True, max_length=128,
                            return_overflowing_tokens=True, padding=True, return_tensors='pt')
        encoded.pop('overflow_to_sample_mapping', None)
        with torch.inference_mode():
            chunk_scores = app.state.model(**encoded).logits.softmax(-1)
        weights = (encoded['attention_mask'].sum(-1) - 2).clamp(min=1)
        scores = (chunk_scores * weights[:, None]).sum(0) / weights.sum()
        labels = sorted([{'name': app.state.model.config.id2label[i], 'score': float(s)}
                         for i, s in enumerate(scores)], key=lambda x: x['score'], reverse=True)
        return {'model': MODEL, 'revision': REVISION, 'labels': labels,
                'self_reported_stress': diary.self_reported_stress,
                'chunks': len(chunk_scores), 'aggregation': 'token_weighted_mean',
                'disclaimer': '분류 점수는 실제 감정 비율이 아니에요. 최종 마음은 직접 선택해주세요.'}
    finally:
        inference_lock.release()


@app.post('/api/healing/recommend')
def recommend_healing(request: HealingRequest):
    """감정 결과를 읽고 추천 도구가 선택한 카드 목록을 반환한다.

    위치는 명시적으로 허용된 경우에도 장소 추천의 자리표시자만 반환하며 좌표를 저장하지 않는다.
    """
    cards = [
        {'id': 'breathing-1m', 'kind': '호흡', 'title': '1분 호흡하기',
         'description': '복잡한 생각을 잠시 내려놓고 호흡에 집중해보세요.', 'minutes': 1},
        {'id': 'journaling-3m', 'kind': '필사·감정정리', 'title': '감정 정리하기',
         'description': '지금 마음에 남은 생각을 세 문장으로 적어보세요.', 'minutes': 3},
        {'id': 'music-calm', 'kind': '음악', 'title': '차분한 음악 듣기',
         'description': '현재 기분에 맞는 짧은 휴식 음악을 선택해보세요.', 'minutes': 5},
    ]
    if request.emotion in {'불안', '걱정', '스트레스', '답답함'} or request.stress >= 4:
        cards.insert(0, {'id': 'grounding-5-4-3-2-1', 'kind': '감각활동',
                         'title': '5-4-3-2-1 감각 돌아보기',
                         'description': '주변에서 보이는 것과 들리는 것을 천천히 세어보세요.', 'minutes': 5})
    if request.allow_location:
        cards.append({'id': 'nearby-placeholder', 'kind': '장소', 'title': '근처 산책 장소 찾기',
                      'description': '위치 권한을 사용해 안전한 장소를 검색할 수 있어요. 좌표는 저장하지 않습니다.', 'minutes': 20})
    return {'tool': 'recommend_healing', 'emotion': request.emotion,
            'stress': request.stress, 'cards': [card for card in cards if card['minutes'] <= request.minutes or card['minutes'] == 1]}


@app.post('/api/feedback')
def save_user_feedback(feedback: Feedback):
    """동의한 경우에만 원문 없이 추천 카드 평가를 임시 집계한다."""
    if feedback.consent:
        feedback_store.append({'id': str(uuid4()), 'card_id': feedback.card_id,
                               'helpful': feedback.helpful, 'comment': feedback.comment})
    return {'tool': 'save_user_feedback', 'saved': feedback.consent,
            'message': '의견을 저장했어요.' if feedback.consent else '동의하지 않아 저장하지 않았어요.'}


app.mount('/', StaticFiles(directory=ROOT / 'dist', html=True), name='ui')
