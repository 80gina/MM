# Hugging Face Spaces (Docker SDK) 배포용 이미지
# - Space는 7860 포트를 노출하고 비루트 사용자(uid 1000)로 실행한다.
# - 모델을 빌드 시점에 내려받아 이미지에 포함시킨다. 첫 요청 콜드스타트를 없애기 위함.
FROM python:3.12-slim

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface \
    HF_HUB_DISABLE_TELEMETRY=1 \
    PYTHONUNBUFFERED=1

WORKDIR /home/user/app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir torch==2.9.0+cpu --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

# 감정 분류 모델을 빌드 단계에서 캐시에 내려받는다 (버전 고정).
RUN python -c "\
from transformers import AutoTokenizer, AutoModelForSequenceClassification; \
m='GGARA02/kcelectra-korean-emotion'; \
r='2eaf89d8d2cbfd902b93e5ec989db2ec103806fb'; \
AutoTokenizer.from_pretrained(m, revision=r); \
AutoModelForSequenceClassification.from_pretrained(m, revision=r, use_safetensors=True)"

COPY --chown=user server.py coach_agent.py rag.py llm.py \
     feedback_db.py healing_knowledge.py memory_db.py ./
COPY --chown=user index.html app.js styles.css ./dist/

# SQLite 저장 경로. Space 재시작 시 초기화되므로 수집 즉시 집계를 내려받는다.
ENV MINDILY_FEEDBACK_DB=/home/user/app/data/feedback.sqlite3 \
    MINDILY_MEMORY_DB=/home/user/app/data/memory.sqlite3

EXPOSE 7860
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860", "--no-access-log"]
