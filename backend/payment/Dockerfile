FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc curl \
    && rm -rf /var/lib/apt/lists/*

COPY payment/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY payment/src/ ./src/

EXPOSE 8350

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8350"]

