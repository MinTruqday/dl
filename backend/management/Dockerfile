FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY management/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY management/src/ ./src/
COPY core/ ./core/

EXPOSE 8050

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8050"]

