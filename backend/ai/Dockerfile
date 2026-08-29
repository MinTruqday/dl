FROM ghcr.io/astral-sh/uv:latest AS uv-build

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TORCHINDUCTOR_CACHE_DIR=/home/appuser/.cache/torchinductor \
    TORCH_HOME=/home/appuser/.cache/torch \
    HF_HOME=/home/appuser/.cache/huggingface \
    TMPDIR=/home/appuser/.cache/tmp

WORKDIR /app

COPY ai/requirements.txt .
COPY --from=uv-build /uv /usr/local/bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    git \
    ripgrep \
    && mkdir -p /home/appuser/.cache/tmp \
    && uv pip install --system --no-cache \
        --index-strategy unsafe-best-match -r requirements.txt \
    && apt-get purge -y build-essential \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

RUN apt-get update && apt-get install -y --no-install-recommends chromium \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

RUN uv pip install --system --no-cache pytest==8.3.5

RUN groupadd --gid 10001 appuser && useradd --uid 10001 --gid appuser -m -s /bin/bash appuser
RUN mkdir -p /home/appuser/.cache/huggingface /home/appuser/.cache/torchinductor /home/appuser/.cache/torch /home/appuser/.cache/tmp && chown -R appuser:appuser /home/appuser/.cache

COPY --chown=appuser:appuser ai/src/ ./src/

USER 10001:10001
HEALTHCHECK --interval=30s --timeout=20s --start-period=90s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=15)"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
