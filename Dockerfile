FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py .
COPY dist ./dist
ENV HF_HOME=/app/models/cache
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
