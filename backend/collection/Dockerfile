FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y tzdata calibre xvfb && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

COPY collection/requirements.txt .

RUN pip install -q --no-cache-dir -r requirements.txt

RUN playwright install chromium

COPY collection/src/ ./src/

EXPOSE 8000

CMD ["sh", "-c", "rm -rf /tmp/.X11-unix/* /tmp/.X*-lock && Xvfb :99 -screen 0 1280x1024x24 -nolisten tcp & sleep 1 && DISPLAY=:99", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

