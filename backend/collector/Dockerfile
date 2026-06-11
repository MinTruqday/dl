FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y tzdata calibre xvfb && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

COPY collector/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium

COPY collector/src/ ./src/
COPY core/ ./core/

EXPOSE 8250

CMD ["xvfb-run", "-a", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8250"]
