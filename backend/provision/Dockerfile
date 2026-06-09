FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

RUN useradd -m doclibuser && chown -R doclibuser:doclibuser /app
USER doclibuser

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8950"]
