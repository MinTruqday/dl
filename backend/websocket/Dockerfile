FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY websocket/requirements.txt .

RUN pip install -q --no-cache-dir -r requirements.txt

COPY websocket/src/ ./src/

RUN useradd -m doclibuser && chown -R doclibuser:doclibuser /app
USER doclibuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=3)"]

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--ws-max-size", "262144", "--ws-ping-interval", "20", "--ws-ping-timeout", "20"]
