FROM node:24-bookworm-slim AS mcp-build

ARG REQWISE_FIGMA_REV=c6b75b9fc1aa315bc75633bd70b6c9b297d04ce4

RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && git clone https://github.com/hoangpm96/reqwise-figma-mcp.git /opt/doclib-mcp/reqwise \
    && git -C /opt/doclib-mcp/reqwise checkout --detach ${REQWISE_FIGMA_REV} \
    && npm --prefix /opt/doclib-mcp/reqwise ci --include=dev \
    && npm --prefix /opt/doclib-mcp/reqwise run build \
    && npm --prefix /opt/doclib-mcp/reqwise prune --omit=dev \
    && npm install --prefix /opt/doclib-mcp/chrome --omit=dev chrome-devtools-mcp@1.6.0 \
    && rm -rf /var/lib/apt/lists/* /root/.npm

FROM ghcr.io/astral-sh/uv:latest AS uv-build

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TORCHINDUCTOR_CACHE_DIR=/home/appuser/.cache/torchinductor \
    TORCH_HOME=/home/appuser/.cache/torch \
    HF_HOME=/home/appuser/.cache/huggingface \
    TMPDIR=/home/appuser/.cache/tmp

WORKDIR /app

COPY agentic_ai/requirements.txt .
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
    && rm -rf /var/lib/apt/lists/*

COPY --from=mcp-build /usr/local/ /usr/local/
COPY --from=mcp-build /opt/doclib-mcp/ /opt/doclib-mcp/

RUN apt-get update && apt-get install -y --no-install-recommends chromium \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 10001 appuser && useradd --uid 10001 --gid appuser -m -s /bin/bash appuser
RUN mkdir -p /home/appuser/.cache/huggingface /home/appuser/.cache/torchinductor /home/appuser/.cache/torch /home/appuser/.cache/tmp && chown -R appuser:appuser /home/appuser/.cache

COPY --chown=appuser:appuser agentic_ai/src/ ./src/

USER 10001:10001
HEALTHCHECK --interval=30s --timeout=20s --start-period=90s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=15)"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
