FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY notification/requirements.txt .

RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt \
    && groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home --home-dir /home/app --shell /usr/sbin/nologin app

COPY notification/src/ ./src/

RUN chown -R app:app /app

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=20s --start-period=30s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=15)"]

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
