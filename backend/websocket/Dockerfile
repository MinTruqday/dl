FROM python:3.11-slim as builder

WORKDIR /build
COPY websocket/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --user --no-warn-script-location -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

COPY --from=builder /root/.local /root/.local
COPY websocket/src/ ./src/
COPY core/ ./core/
COPY models/ ./models/
COPY websocket/main.py .

EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "1"]
