FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY documents/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY documents/src/ ./src/
COPY shared/ ./shared/

EXPOSE 8450

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8450"]

