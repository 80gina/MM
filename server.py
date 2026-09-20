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
from feedback_db import save_feedback
from healing_knowledge import retrieve_activities
from memory_db import remember, recall, forget
from coach_agent import run_coach_agent
from rag import answer_with_grounding, retrieve_grounding
from comfort_knowledge import comfort_for
import llm

MODEL = os.getenv('MINDILY_MODEL_PATH', 'GGARA02/kcelectra-korean-emotion')
REVISION = '2eaf89d8d2cbfd902b93e5ec989db2ec103806fb'
inference_lock = Lock()


@asynccontextmanager
async def lifespan(app):
    offline = os.getenv('MINDILY_OFFLINE') == '1'
    model_source = Path(MODEL)
    load_args = {'local_files_only': offline}
    if not model_source.exists():
        load_args['revision'] = REVISION
    app.state.tokenizer = AutoTokenizer.from_pretrained(MODEL, **load_args)
    app.state.model = AutoModelForSequenceClassification.from_pretrained(
        MODEL, **load_args, use_safetensors=True
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


class AgentRequest(Diary):
    context: str = Field(default='diary', pattern='^(diary|chat)$')
    memory_token: Optional[str] = Field(default=None, min_length=32, max_length=128)
    known_emotion: Optional[str] = Field(default=None, pattern='^(불안|슬픔|분노|기쁨|상처|당황)$')


class HealingRequest(BaseModel):
    emotion: str = Field(min_length=1, max_length=30)
    stress: int = Field(ge=1, le=5, strict=True)
    minutes: int = Field(default=5, ge=1, le=120, strict=True)
    allow_location: bool = False
    memory_token: Optional[str] = Field(default=None, min_length=32, max_length=128)


class MemoryRequest(BaseModel):
    token: str = Field(min_length=32, max_length=128)


class MemorySave(MemoryRequest):
    preferred_kind: str = Field(pattern='^(호흡|감각활동|걷기)$')
    consent: bool


class Feedback(BaseModel):
    card_id: str = Field(min_length=1, max_length=80)
    helpful: Optional[bool] = None
    satisfaction: Optional[int] = Field(default=None, ge=1, le=5, strict=True)
    comment: Optional[str] = Field(default=None, max_length=300)
    consent: bool = False


@app.get('/api/health')
def health():
    return {'status': 'ready', 'model': MODEL,
            'revision': REVISION if not Path(MODEL).exists() else 'local-fine-tuned',
            'generation': llm.status()}


@app.get('/api/llm/status')
def llm_status():
    """생성형 경로의 활성 여부와 접지 정책을 공개한다. API 키는 노출하지 않는다."""
    return llm.status()


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
        return {'model': MODEL, 'revision': REVISION if not Path(MODEL).exists() else 'local-fine-tuned', 'labels': labels,
                'self_reported_stress': diary.self_reported_stress,
                'chunks': len(chunk_scores), 'aggregation': 'token_weighted_mean',
                'disclaimer': '분류 점수는 실제 감정 비율이 아니에요. 최종 마음은 직접 선택해주세요.'}
    finally:
        inference_lock.release()


@app.post('/api/healing/recommend')
def recommend_healing(request: HealingRequest):
    """Retrieve sourced activities; location lookup is not implemented yet."""
    cards = retrieve_activities(request.emotion, request.stress, request.minutes)
    preferred = recall(request.memory_token) if request.memory_token else None
    if preferred:
        cards.sort(key=lambda card: card['kind'] == preferred, reverse=True)
    return {'tool': 'recommend_healing', 'emotion': request.emotion,
            'stress': request.stress, 'cards': cards,
            'location_available': False, 'personalized': bool(preferred)}


@app.post('/api/rag/search')
def rag_search(request: HealingRequest):
    """Return source chunks selected for a grounded response."""
    return {'tool': 'retrieve_grounding', 'emotion': request.emotion,
            'stress': request.stress, 'sources': retrieve_grounding(
                request.emotion, request.stress, request.minutes)}


@app.post('/api/rag/answer')
def rag_answer(request: HealingRequest):
    """Return a grounded fallback answer and its source context."""
    return {'tool': 'rag_answer', 'emotion': request.emotion,
            'stress': request.stress, **answer_with_grounding(
                request.emotion, request.stress, request.minutes)}


@app.post('/api/agent/coach')
def coach(request: AgentRequest):
    """Route a diary or chat turn through the real model and sourced activity tool."""
    result = run_coach_agent(
        request.text, request.self_reported_stress, request.context, request.memory_token,
        lambda text, stress: analyze(Diary(text=text, self_reported_stress=stress)),
        lambda emotion, stress, token: recommend_healing(
            HealingRequest(emotion=emotion, stress=stress, minutes=20, memory_token=token)),
        request.known_emotion,
        lambda emotion, stress: answer_with_grounding(emotion, stress, minutes=20),
    )
    analysis = result.get('analysis')
    lead = analysis['labels'][0]['name'] if analysis else (request.known_emotion or '불안')
    result['comfort'] = comfort_for(lead)
    return result


@app.post('/api/memory')
def save_memory(request: MemorySave):
    if not request.consent:
        raise HTTPException(422, '기억 저장 동의가 필요해요.')
    remember(request.token, request.preferred_kind)
    return {'saved': True, 'preferred_kind': request.preferred_kind}


@app.post('/api/memory/read')
def read_memory(request: MemoryRequest):
    return {'preferred_kind': recall(request.token)}


@app.post('/api/memory/delete')
def delete_memory(request: MemoryRequest):
    return {'deleted': forget(request.token)}


@app.post('/api/feedback')
def save_user_feedback(feedback: Feedback):
    """Store consented feedback in SQLite; diary text and location are never included."""
    if not feedback.consent:
        return {'tool': 'save_user_feedback', 'saved': False,
                'message': '동의하지 않아 저장하지 않았어요.'}
    if feedback.satisfaction is None and feedback.helpful is None:
        raise HTTPException(422, '만족도 또는 도움됨 평가를 선택해주세요.')
    helpful = feedback.helpful if feedback.helpful is not None else feedback.satisfaction >= 4
    receipt = save_feedback(feedback.card_id, helpful, feedback.satisfaction, feedback.comment)
    return {'tool': 'save_user_feedback', 'saved': True,
            'receipt': receipt, 'message': '의견을 저장했어요.'}


app.mount('/', StaticFiles(directory=ROOT / 'dist', html=True), name='ui')
