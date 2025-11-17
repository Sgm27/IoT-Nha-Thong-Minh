#!/bin/bash
#
# Build Docker image cho IoT Client
#

set -e

echo "=========================================="
echo "  Building IoT Client Docker Image"
echo "=========================================="
echo ""

cd "$(dirname "$0")/.."

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile không tìm thấy!"
    exit 1
fi

# Build image
echo "Building Docker image..."
docker build -t iot-smart-home-client:latest .

echo ""
echo "✓ Build hoàn tất!"
echo ""
echo "Image: iot-smart-home-client:latest"
echo ""
echo "Để chạy:"
echo "  docker-compose up -d"
echo ""
