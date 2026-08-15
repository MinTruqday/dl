FROM ghcr.io/astral-sh/uv:latest AS uv-build

FROM debian:bookworm-slim AS llama-build

ARG LLAMA_CPP_REV=305ba519ab61cdff8044922cba2347826a04453f

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates cmake git \
    && git init /opt/llama.cpp \
    && git -C /opt/llama.cpp remote add origin https://github.com/ggml-org/llama.cpp.git \
    && git -C /opt/llama.cpp fetch --depth 1 origin ${LLAMA_CPP_REV} \
    && git -C /opt/llama.cpp checkout --detach FETCH_HEAD \
    && cmake -S /opt/llama.cpp -B /opt/llama.cpp/build \
        -DGGML_NATIVE=OFF -DLLAMA_CURL=OFF -DGGML_OPENMP=OFF \
    && cmake --build /opt/llama.cpp/build --config Release \
        --target llama-quantize -j6 \
    && rm -rf /var/lib/apt/lists/*

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TORCHINDUCTOR_CACHE_DIR=/home/appuser/.cache/torchinductor \
    TORCH_HOME=/home/appuser/.cache/torch \
    HF_HOME=/home/appuser/.cache/huggingface \
    TMPDIR=/home/appuser/.cache/tmp

WORKDIR /app
COPY --from=uv-build /uv /usr/local/bin/uv
COPY finetune/requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && uv pip install --system --no-cache \
        --index-strategy unsafe-best-match -r requirements.txt \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser -m -s /bin/bash appuser \
    && mkdir -p /home/appuser/.cache/huggingface \
        /home/appuser/.cache/torchinductor \
        /home/appuser/.cache/torch \
        /home/appuser/.cache/tmp \
        /var/lib/doclib/finetune/models \
        /var/lib/doclib/finetune/adapters \
        /var/lib/doclib/finetune/gguf \
    && chown -R appuser:appuser /home/appuser/.cache /var/lib/doclib

COPY --from=llama-build --chown=appuser:appuser /opt/llama.cpp /app/llama.cpp
COPY --chown=appuser:appuser finetune/src/ ./src/

USER 10001:10001
HEALTHCHECK --interval=30s --timeout=20s --start-period=90s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=15)"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
