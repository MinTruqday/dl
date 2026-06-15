FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY agentic_ai/requirements.txt .
RUN pip install --no-cache-dir torch>=2.2.0
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-vie \
    tesseract-ocr-eng \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

RUN useradd -m -s /bin/bash appuser
RUN mkdir -p /home/appuser/.cache/huggingface && chown -R appuser:appuser /home/appuser/.cache
RUN mkdir -p /tmp/doclib_finetune/models /tmp/doclib_finetune/adapters /tmp/doclib_finetune/gguf && chown -R appuser:appuser /tmp/doclib_finetune
COPY --chown=appuser:appuser agentic_ai/src/ ./src/
COPY --chown=appuser:appuser core/ ./core/

USER appuser

EXPOSE 8000

CMD ["bash", "-c", "gunicorn src.main:app -w 1 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --timeout 1200"]

