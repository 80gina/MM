FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py feedback_db.py healing_knowledge.py memory_db.py ./
COPY dist ./dist
ENV HF_HOME=/app/models/cache
VOLUME ["/app/data", "/app/models"]
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
