
FROM python:3.12-slim AS builder

WORKDIR /app


RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt gunicorn uvicorn[standard]


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
    PATH="/home/appuser/.local/bin:${PATH}"

WORKDIR /app


RUN useradd -m -s /bin/bash appuser

COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8001


CMD ["gunicorn", "src.main:app", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8001"]
