FROM python:3.11-slim as builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --user --no-warn-script-location -r requirements.txt

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates fontconfig calibre \
    && ARCH=$(uname -m) && \
    if [ "$ARCH" = "aarch64" ]; then \
        URL="https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-aarch64-unknown-linux-musl.tar.gz"; \
    else \
        URL="https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-x86_64-unknown-linux-gnu.tar.gz"; \
    fi && \
    curl -fsSL "$URL" | tar -xz -C /usr/local/bin/ tectonic \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONPATH=/root/.local
ENV PATH=/root/.local/bin:$PATH
ENV HOST=0.0.0.0
ENV PORT=8000

COPY --from=builder /root/.local /root/.local
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
