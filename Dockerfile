FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip wheel setuptools && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app

# создать пользователя и подготовить его $HOME/.cache с правами
RUN useradd -m botuser && \
    mkdir -p /home/botuser/.cache && \
    chown -R botuser:botuser /home/botuser /app

USER botuser

# единый путь для всех кешей (Whisper, Argos)
ENV XDG_CACHE_HOME=/home/botuser/.cache

CMD ["python", "main.py"]
