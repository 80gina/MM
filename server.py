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

MODEL = 'GGARA02/kcelectra-korean-emotion'
REVISION = '2eaf89d8d2cbfd902b93e5ec989db2ec103806fb'
inference_lock = Lock()


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


app.mount('/', StaticFiles(directory=ROOT / 'dist', html=True), name='ui')
