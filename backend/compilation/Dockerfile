FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates fontconfig pandoc ghostscript \
    fonts-wine \
    libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
    libcairo2 libgdk-pixbuf-2.0-0 libffi-dev \
    fonts-dejavu fonts-liberation fonts-noto-cjk \
    && fc-cache -f -v \
    && ARCH=$(uname -m) && \
    if [ "$ARCH" = "aarch64" ]; then \
    URL="https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-aarch64-unknown-linux-musl.tar.gz"; \
    else \
    URL="https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-x86_64-unknown-linux-gnu.tar.gz"; \
    fi && \
    curl -fsSL "$URL" | tar -xz -C /usr/local/bin/ tectonic \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY compilation/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY compilation/src/ ./src/

RUN useradd -m doclibuser && chown -R doclibuser:doclibuser /app
USER doclibuser

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8011"]

