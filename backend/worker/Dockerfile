FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY worker/requirements.txt .

RUN pip install -q --user --no-cache-dir -r requirements.txt

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates fontconfig \
    && ARCH=$(uname -m) && \
    if [ "$ARCH" = "aarch64" ]; then \
    URL="https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-aarch64-unknown-linux-musl.tar.gz"; \
    else \
    URL="https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-x86_64-unknown-linux-gnu.tar.gz"; \
    fi && \
    curl -fsSL "$URL" | tar -xz -C /usr/local/bin/ tectonic \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME="/home/appuser" \
    PIP_CACHE_DIR="/tmp/pip-cache" \
    PATH="/home/appuser/.local/bin:${PATH}"

WORKDIR /app

RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser -m -s /bin/bash appuser \
    && mkdir -p /tmp/pip-cache \
    && chown -R appuser:appuser /tmp/pip-cache

COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local
COPY --chown=appuser:appuser worker/src/ ./src/

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=20s --start-period=30s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=15)"]

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
