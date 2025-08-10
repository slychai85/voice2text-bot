FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ffmpeg + libgomp1 для faster-whisper (CTranslate2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libgomp1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip wheel setuptools && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app

# Пользователь без root и права на кеш
RUN useradd -m botuser && \
    mkdir -p /home/botuser/.cache && \
    chown -R botuser:botuser /home/botuser /app

USER botuser

# Единый кеш для Whisper/Argos
ENV XDG_CACHE_HOME=/home/botuser/.cache

CMD ["python", "main.py"]
