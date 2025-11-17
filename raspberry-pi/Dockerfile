# Dockerfile cho IoT Client - Raspberry Pi 5
# Multi-stage build để giảm image size

FROM python:3.11-slim-bookworm AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    pkg-config \
    wget \
    # PyAudio build dependencies
    portaudio19-dev \
    libasound2-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python packages
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt


# Final stage
FROM python:3.11-slim-bookworm

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # GPIO access
    gpiod \
    libgpiod2 \
    # OpenCV dependencies (minimal for mock mode)
    libopencv-dev \
    libatlas-base-dev \
    libhdf5-dev \
    libhdf5-serial-dev \
    libharfbuzz0b \
    libwebp7 \
    libgstreamer1.0-0 \
    libavcodec59 \
    libavformat59 \
    libswscale6 \
    libv4l-dev \
    # Audio dependencies
    portaudio19-dev \
    libportaudio2 \
    libasound2-dev \
    alsa-utils \
    # Utilities
    v4l-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create app directory
WORKDIR /app

# Copy application code
COPY src/ /app/src/
COPY config/ /app/config/

# Create log directory
RUN mkdir -p /var/log

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run as non-root user for security (but will need privileged for GPIO)
# RUN useradd -m -u 1000 iotuser && chown -R iotuser:iotuser /app
# USER iotuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Entrypoint
CMD ["python", "-u", "src/iot_client.py"]
