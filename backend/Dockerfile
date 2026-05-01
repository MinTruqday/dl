FROM python:3.11-slim as builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --user --no-warn-script-location -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/root/.local
ENV PATH=/root/.local/bin:$PATH
ENV HOST=0.0.0.0
ENV PORT=8000

COPY --from=builder /root/.local /root/.local
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
