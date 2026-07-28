FROM python:3.11-slim

ARG LLAMA_CPP_REV=305ba519ab61cdff8044922cba2347826a04453f

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TORCHINDUCTOR_CACHE_DIR=/home/appuser/.cache/torchinductor \
    TORCH_HOME=/home/appuser/.cache/torch \
    HF_HOME=/home/appuser/.cache/huggingface \
    TMPDIR=/home/appuser/.cache/tmp

WORKDIR /app

COPY agentic_ai/requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    git \
    ripgrep \
    && pip install -q --no-cache-dir -r requirements.txt \
    && apt-get purge -y build-essential \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash appuser
RUN mkdir -p /home/appuser/.cache/huggingface /home/appuser/.cache/torchinductor /home/appuser/.cache/torch /home/appuser/.cache/tmp /var/lib/doclib/finetune/models /var/lib/doclib/finetune/adapters /var/lib/doclib/finetune/gguf && chown -R appuser:appuser /home/appuser/.cache /var/lib/doclib
RUN git init /app/llama.cpp && \
    git -C /app/llama.cpp remote add origin https://github.com/ggerganov/llama.cpp.git && \
    git -C /app/llama.cpp fetch --depth 1 origin ${LLAMA_CPP_REV} && \
    git -C /app/llama.cpp checkout --detach FETCH_HEAD && \
    chown -R appuser:appuser /app/llama.cpp

COPY --chown=appuser:appuser agentic_ai/src/ ./src/

USER appuser
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=3)"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
