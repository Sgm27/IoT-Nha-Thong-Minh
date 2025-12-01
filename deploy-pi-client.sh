#!/bin/bash
# Deploy chỉ raspberry-pi client code lên Pi (không dùng Docker)

set -e

PI_USER="${1:-pi}"
PI_HOST="${2:-raspberrypi.local}"
PI_DIR="/home/pi/raspberry-pi"

echo "========================================="
echo "  Deploy Raspberry Pi Client"
echo "========================================="
echo "User: ${PI_USER}"
echo "Host: ${PI_HOST}"
echo ""

# Test connection
echo "Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 ${PI_USER}@${PI_HOST} "echo 'Connected!'" 2>/dev/null; then
    echo "❌ Cannot connect to Pi at ${PI_HOST}"
    echo ""
    echo "Usage: $0 [pi_user] [pi_host]"
    echo "Example: $0 pi 169.254.165.225"
    echo "Example: $0 pi raspberrypi.local"
    exit 1
fi

echo "✅ Connected to ${PI_HOST}"

# Upload files using rsync
echo ""
echo "Uploading raspberry-pi directory..."

rsync -avz --progress \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='*.log' \
    raspberry-pi/ ${PI_USER}@${PI_HOST}:${PI_DIR}/

echo "✅ Upload complete!"

echo ""
echo "========================================="
echo "  ✅ Deployment Complete!"
echo "========================================="
echo ""
echo "Files deployed to: ${PI_USER}@${PI_HOST}:${PI_DIR}"
echo ""
echo "Next steps:"
echo ""
echo "1. SSH to Pi:"
echo "   ssh ${PI_USER}@${PI_HOST}"
echo ""
echo "2. Run the IoT client:"
echo "   cd ~/raspberry-pi"
echo "   sudo ./venv/bin/python3 src/iot_client.py"
echo ""
echo "Or test hardware first:"
echo "   sudo ./venv/bin/python3 scripts/test-hardware.py"
echo ""
