# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# --- Install system dependencies (OpenCV & build tools) ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# --- Install Python dependencies first to leverage cache ---
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Copy backend source code ---
COPY backend ./backend

WORKDIR /app/backend

EXPOSE 8000

# --- Run the app ---
CMD ["uvicorn", "app.main:create_app", "--host", "0.0.0.0", "--port", "8000"]
