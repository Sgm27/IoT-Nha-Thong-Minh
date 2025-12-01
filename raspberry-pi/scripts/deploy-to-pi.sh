#!/bin/bash
# Deploy script - Push project to Raspberry Pi and setup

set -e

# Configuration
PI_USER="pi"
PI_HOST="raspberry.local"  # Hoặc dùng IP: 169.254.165.225
PI_PASSWORD="1012004"
PI_PROJECT_DIR="/home/pi/IoT-Nha-Thong-Minh/raspberry-pi"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deploying to Raspberry Pi${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if sshpass is installed (for password authentication)
if ! command -v sshpass &> /dev/null; then
    echo -e "${YELLOW}⚠️  sshpass not found. Installing...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install hudochenkov/sshpass/sshpass
    else
        # Linux
        sudo apt-get install -y sshpass
    fi
fi

# Test SSH connection
echo -e "\n${YELLOW}🔍 Testing SSH connection to ${PI_USER}@${PI_HOST}...${NC}"
if sshpass -p "${PI_PASSWORD}" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 ${PI_USER}@${PI_HOST} "echo 'Connection successful!'" 2>/dev/null; then
    echo -e "${GREEN}✅ SSH connection OK!${NC}"
else
    echo -e "${RED}❌ Cannot connect to Pi. Trying IP address...${NC}"
    PI_HOST="169.254.165.225"
    if sshpass -p "${PI_PASSWORD}" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 ${PI_USER}@${PI_HOST} "echo 'Connection successful!'" 2>/dev/null; then
        echo -e "${GREEN}✅ SSH connection OK using IP!${NC}"
    else
        echo -e "${RED}❌ Cannot connect to Raspberry Pi at ${PI_HOST}${NC}"
        echo -e "${YELLOW}Please check:${NC}"
        echo "  1. Pi is powered on"
        echo "  2. Pi is connected to same network"
        echo "  3. Hostname/IP is correct"
        echo "  4. SSH is enabled on Pi (sudo raspi-config)"
        exit 1
    fi
fi

# Create project directory on Pi
echo -e "\n${YELLOW}📁 Creating project directory on Pi...${NC}"
sshpass -p "${PI_PASSWORD}" ssh ${PI_USER}@${PI_HOST} "mkdir -p ${PI_PROJECT_DIR}"

# Get current directory (should be raspberry-pi/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "\n${YELLOW}📦 Syncing project files to Pi...${NC}"
echo "From: ${PROJECT_DIR}"
echo "To: ${PI_USER}@${PI_HOST}:${PI_PROJECT_DIR}"

# Use rsync to sync files (excluding unnecessary files)
sshpass -p "${PI_PASSWORD}" rsync -avz --progress \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.env' \
    --exclude 'venv' \
    --exclude '.DS_Store' \
    --exclude 'node_modules' \
    -e "ssh -o StrictHostKeyChecking=no" \
    "${PROJECT_DIR}/" \
    ${PI_USER}@${PI_HOST}:${PI_PROJECT_DIR}/

echo -e "${GREEN}✅ Files synced successfully!${NC}"

# Run setup on Pi
echo -e "\n${YELLOW}⚙️  Running setup on Raspberry Pi...${NC}"

sshpass -p "${PI_PASSWORD}" ssh ${PI_USER}@${PI_HOST} << 'ENDSSH'
cd /home/pi/IoT-Nha-Thong-Minh/raspberry-pi

echo "========================================="
echo "  Installing system dependencies"
echo "========================================="

# Update package list
sudo apt-get update

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
echo "========================================="
echo "  Setting up Python environment"
echo "========================================="

# Create virtual environment
python3 -m venv venv

# Activate venv and install dependencies
source venv/bin/activate

pip install --upgrade pip

# Install Python packages
pip install -r requirements.txt

echo ""
echo "========================================="
echo "  Configuration"
echo "========================================="

# Create .env file if not exists
if [ ! -f "config/.env" ]; then
    echo "Creating .env file from example..."
    cp config/.env.example config/.env

    echo ""
    echo "⚠️  Please edit config/.env to set your backend WebSocket URL!"
    echo "   Current setting: ws://localhost:8000/ws/gemini"
    echo ""
fi

echo ""
echo "========================================="
echo "  ✅ Setup complete!"
echo "========================================="
echo ""
echo "To run the IoT client:"
echo "  1. Edit config: nano config/.env"
echo "  2. Run: cd /home/pi/IoT-Nha-Thong-Minh/raspberry-pi && source venv/bin/activate && python src/iot_client.py"
echo ""
echo "Or use systemd service:"
echo "  sudo ./scripts/install-service.sh"
echo ""

ENDSSH

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  ✅ Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "  1. SSH to Pi: ssh pi@${PI_HOST}"
echo "  2. Edit config: nano /home/pi/IoT-Nha-Thong-Minh/raspberry-pi/config/.env"
echo "  3. Run client: cd /home/pi/IoT-Nha-Thong-Minh/raspberry-pi && source venv/bin/activate && python src/iot_client.py"
echo ""
echo -e "${YELLOW}Or install as systemd service:${NC}"
echo "  ssh pi@${PI_HOST}"
echo "  cd /home/pi/IoT-Nha-Thong-Minh/raspberry-pi"
echo "  sudo ./scripts/install-service.sh"
echo ""
