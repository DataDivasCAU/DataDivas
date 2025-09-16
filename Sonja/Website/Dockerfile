# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# (optional) Systempakete
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Dependencies installieren
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# App-Code + Templates + Daten
COPY . /app

EXPOSE 8000

# Gunicorn = Production Server
CMD ["gunicorn", "-w", "2", "-k", "gthread", "-b", "0.0.0.0:8000", "app:app"]
