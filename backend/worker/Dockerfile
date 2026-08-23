FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY worker/src/ ./src/

RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser -m -s /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=20s --start-period=10s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=15)"]

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
