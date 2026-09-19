FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir torch==2.9.0+cpu --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir -r requirements.txt
COPY server.py coach_agent.py feedback_db.py healing_knowledge.py memory_db.py ./
COPY dist ./dist
ENV HF_HOME=/app/data/hf-cache
EXPOSE 8000
CMD ["sh", "-c", "exec python -m uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000} --no-access-log"]
