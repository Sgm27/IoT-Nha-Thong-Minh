#!/bin/bash
# Deploy toàn bộ project (backend + raspberry-pi) lên Pi và chạy với docker-compose

set -e

PI_USER="pi"
PI_HOST="raspberry.local"
PI_DIR="/home/pi/IoT-Nha-Thong-Minh"

echo "========================================="
echo "  Deploy Full Stack to Raspberry Pi"
echo "========================================="

# Test connection
echo "Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 ${PI_USER}@${PI_HOST} "echo 'Connected!'" 2>/dev/null; then
    echo "Cannot connect to Pi. Trying IP..."
    PI_HOST="169.254.165.225"
    if ! ssh -o ConnectTimeout=5 ${PI_USER}@${PI_HOST} "echo 'Connected!'" 2>/dev/null; then
        echo "❌ Cannot connect to Pi!"
        exit 1
    fi
fi

echo "✅ Connected to ${PI_HOST}"

# Create tarball
echo ""
echo "Creating tarball..."
TARBALL="/tmp/iot-full.tar.gz"

tar -czf "$TARBALL" \
    --exclude='.git' \
    --exclude='**/node_modules' \
    --exclude='**/__pycache__' \
    --exclude='**/*.pyc' \
    --exclude='**/venv' \
    --exclude='.DS_Store' \
    --exclude='**/.env' \
    docker-compose.yml \
    backend/ \
    raspberry-pi/

echo "✅ Tarball created: $(du -h $TARBALL | cut -f1)"

# Upload
echo ""
echo "Uploading to Pi..."
ssh ${PI_USER}@${PI_HOST} "mkdir -p ${PI_DIR}"
scp "$TARBALL" ${PI_USER}@${PI_HOST}:/tmp/

echo "✅ Uploaded"

# Extract and setup
echo ""
echo "Setting up on Pi..."

ssh ${PI_USER}@${PI_HOST} << 'ENDSSH'
cd ~/IoT-Nha-Thong-Minh
tar -xzf /tmp/iot-full.tar.gz
rm /tmp/iot-full.tar.gz

echo "✅ Files extracted"

# Create .env files
echo ""
echo "Creating config files..."

# Backend .env
if [ ! -f "backend/.env" ]; then
    cat > backend/.env << 'EOF'
GEMINI_API_KEY=your_api_key_here
PORT=8000
EOF
    echo "⚠️  Created backend/.env - PLEASE ADD YOUR GEMINI_API_KEY!"
else
    echo "✅ backend/.env already exists"
fi

# Raspberry-pi .env
if [ ! -f "raspberry-pi/config/.env" ]; then
    cp raspberry-pi/config/.env.example raspberry-pi/config/.env 2>/dev/null || \
    cat > raspberry-pi/config/.env << 'EOF'
WEBSOCKET_SERVER_URL=ws://localhost:8000/ws/gemini
CAMERA_DEVICE_INDEX=0
CAMERA_WIDTH=1280
CAMERA_HEIGHT=720
CAMERA_FPS=30
MOCK_MODE=false
EOF
    echo "✅ Created raspberry-pi/config/.env"
else
    echo "✅ raspberry-pi/config/.env already exists"
fi

echo ""
echo "========================================="
echo "  ✅ Setup Complete!"
echo "========================================="

ENDSSH

# Cleanup
rm -f "$TARBALL"

echo ""
echo "========================================="
echo "  Next Steps on Pi:"
echo "========================================="
echo ""
echo "1. SSH to Pi:"
echo "   ssh pi@${PI_HOST}"
echo ""
echo "2. Edit backend/.env and add GEMINI_API_KEY:"
echo "   cd ~/IoT-Nha-Thong-Minh"
echo "   nano backend/.env"
echo ""
echo "3. Run everything with docker-compose:"
echo "   docker-compose --profile raspberry-pi up -d"
echo ""
echo "4. View logs:"
echo "   docker-compose logs -f"
echo ""
echo "5. Stop everything:"
echo "   docker-compose --profile raspberry-pi down"
echo ""
