FROM python:3.11-slim

ARG LLAMA_CPP_REV=305ba519ab61cdff8044922cba2347826a04453f

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY agentic_ai/requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    ffmpeg \
    git \
    ripgrep \
    && pip install -q --no-cache-dir -r requirements.txt \
    && apt-get purge -y build-essential \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash appuser
RUN mkdir -p /home/appuser/.cache/huggingface && chown -R appuser:appuser /home/appuser/.cache
RUN mkdir -p /tmp/doclib_finetune/models /tmp/doclib_finetune/adapters /tmp/doclib_finetune/gguf && chown -R appuser:appuser /tmp/doclib_finetune

RUN git init /app/llama.cpp && \
    git -C /app/llama.cpp remote add origin https://github.com/ggerganov/llama.cpp.git && \
    git -C /app/llama.cpp fetch --depth 1 origin ${LLAMA_CPP_REV} && \
    git -C /app/llama.cpp checkout --detach FETCH_HEAD && \
    chown -R appuser:appuser /app/llama.cpp

COPY --chown=appuser:appuser agentic_ai/src/ ./src/

USER appuser
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
