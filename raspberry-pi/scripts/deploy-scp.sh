#!/bin/bash
# Deploy script using SCP - Push project to Raspberry Pi

set -e

# Configuration
PI_USER="pi"
PI_HOST="raspberry.local"  # Hoặc: 169.254.165.225
PI_PASSWORD="1012004"
PI_PROJECT_DIR="/home/pi/IoT-Nha-Thong-Minh/raspberry-pi"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deploy to Raspberry Pi (SCP)${NC}"
echo -e "${GREEN}========================================${NC}"

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_NAME="raspberry-pi"

echo -e "\n${YELLOW}📁 Project directory: ${PROJECT_DIR}${NC}"

# Step 1: Test SSH connection
echo -e "\n${YELLOW}🔍 Testing SSH connection to ${PI_USER}@${PI_HOST}...${NC}"

if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no ${PI_USER}@${PI_HOST} "echo 'Connected!'" 2>/dev/null; then
    echo -e "${GREEN}✅ SSH connection OK!${NC}"
else
    echo -e "${RED}❌ Cannot connect to Pi${NC}"
    echo -e "${YELLOW}Trying IP address instead...${NC}"
    PI_HOST="169.254.165.225"

    if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no ${PI_USER}@${PI_HOST} "echo 'Connected!'" 2>/dev/null; then
        echo -e "${GREEN}✅ SSH connection OK using IP!${NC}"
    else
        echo -e "${RED}❌ Cannot connect to Raspberry Pi${NC}"
        echo -e "${YELLOW}Please check:${NC}"
        echo "  1. Pi is powered on"
        echo "  2. Pi is connected to same network"
        echo "  3. SSH is enabled (sudo raspi-config → Interface → SSH)"
        echo "  4. Try: ssh pi@raspberry.local or ssh pi@169.254.165.225"
        exit 1
    fi
fi

# Step 2: Create project directory on Pi
echo -e "\n${YELLOW}📁 Creating project directory on Pi...${NC}"
ssh ${PI_USER}@${PI_HOST} "mkdir -p ${PI_PROJECT_DIR}"
echo -e "${GREEN}✅ Directory created${NC}"

# Step 3: Create tarball (excluding unnecessary files)
echo -e "\n${YELLOW}📦 Creating tarball...${NC}"
cd "$PROJECT_DIR"

TARBALL="/tmp/${PROJECT_NAME}.tar.gz"

tar -czf "$TARBALL" \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='venv' \
    --exclude='.DS_Store' \
    --exclude='node_modules' \
    --exclude='*.tar.gz' \
    .

TARBALL_SIZE=$(du -h "$TARBALL" | cut -f1)
echo -e "${GREEN}✅ Tarball created: ${TARBALL} (${TARBALL_SIZE})${NC}"

# Step 4: Copy tarball to Pi using SCP
echo -e "\n${YELLOW}📤 Uploading to Pi with SCP...${NC}"
scp -o StrictHostKeyChecking=no "$TARBALL" ${PI_USER}@${PI_HOST}:/tmp/

echo -e "${GREEN}✅ Upload complete!${NC}"

# Step 5: Extract on Pi and setup
echo -e "\n${YELLOW}📂 Extracting and setting up on Pi...${NC}"

ssh ${PI_USER}@${PI_HOST} << ENDSSH
    echo "Extracting tarball..."
    cd ${PI_PROJECT_DIR}
    tar -xzf /tmp/${PROJECT_NAME}.tar.gz
    rm /tmp/${PROJECT_NAME}.tar.gz

    echo "✅ Files extracted!"

    echo ""
    echo "========================================="
    echo "  Installing dependencies"
    echo "========================================="

    # Update package list
    sudo apt-get update -qq

    # Install system dependencies
    sudo apt-get install -y \
        python3-pip \
        python3-venv \
        python3-dev \
        libgpiod2 \
        python3-opencv \
        portaudio19-dev \
        libasound2-dev \
        v4l-utils

    echo ""
    echo "Setting up Python environment..."

    # Create venv if not exists
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi

    # Install Python packages
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q

    echo ""
    echo "Creating config file..."

    # Create .env if not exists
    if [ ! -f "config/.env" ]; then
        cp config/.env.example config/.env
        echo "⚠️  Created config/.env - please edit it!"
    fi

    echo ""
    echo "========================================="
    echo "  ✅ Setup Complete!"
    echo "========================================="
    echo ""
    echo "Files deployed to: ${PI_PROJECT_DIR}"
    ls -lh
ENDSSH

# Cleanup local tarball
echo -e "\n${YELLOW}🧹 Cleaning up...${NC}"
rm -f "$TARBALL"
echo -e "${GREEN}✅ Local tarball removed${NC}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  ✅ Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "  1. SSH to Pi:"
echo "     ${GREEN}ssh pi@${PI_HOST}${NC}"
echo ""
echo "  2. Edit config:"
echo "     ${GREEN}nano ${PI_PROJECT_DIR}/config/.env${NC}"
echo "     (Set WEBSOCKET_SERVER_URL to your backend IP)"
echo ""
echo "  3. Test hardware:"
echo "     ${GREEN}cd ${PI_PROJECT_DIR}${NC}"
echo "     ${GREEN}./scripts/test-simple.sh${NC}"
echo ""
echo "  4. Run IoT client:"
echo "     ${GREEN}cd ${PI_PROJECT_DIR}${NC}"
echo "     ${GREEN}source venv/bin/activate${NC}"
echo "     ${GREEN}python src/iot_client.py${NC}"
echo ""
echo "  5. Or install as service:"
echo "     ${GREEN}cd ${PI_PROJECT_DIR}${NC}"
echo "     ${GREEN}sudo ./scripts/install-service.sh${NC}"
echo ""
