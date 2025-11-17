#!/bin/bash
#
# Run IoT Client trong MOCK MODE (không cần hardware)
# Hữu ích để test trên máy development
#

set -e

cd "$(dirname "$0")/.."

echo "=========================================="
echo "  IoT Client - MOCK MODE"
echo "  (Không cần GPIO/Camera/Audio thật)"
echo "=========================================="
echo ""

# Run with docker-compose and override environment
echo "Starting container in MOCK mode..."
MOCK_MODE=true docker-compose run --rm -e MOCK_MODE=true iot-client

echo ""
echo "✓ Container đã dừng"
echo ""
