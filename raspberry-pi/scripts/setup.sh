#!/bin/bash
#
# Setup script cho IoT Client trên Raspberry Pi 5
#

set -e

echo "=========================================="
echo "  IoT Smart Home Client - Setup"
echo "  Raspberry Pi 5"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo -e "${YELLOW}Cảnh báo: Có vẻ không phải Raspberry Pi${NC}"
else
    MODEL=$(cat /proc/device-tree/model)
    echo -e "${GREEN}Detected: $MODEL${NC}"
fi

echo ""
echo "=== Bước 1: Cập nhật hệ thống ==="
sudo apt-get update
sudo apt-get upgrade -y

echo ""
echo "=== Bước 2: Cài đặt system dependencies ==="

# Python 3.11+
echo "Cài đặt Python 3 và pip..."
sudo apt-get install -y python3 python3-pip python3-venv

# OpenCV dependencies
echo "Cài đặt OpenCV dependencies..."
sudo apt-get install -y \
    libopencv-dev \
    python3-opencv \
    libatlas-base-dev \
    libjasper-dev \
    libqt4-test \
    libqtgui4

# PyAudio dependencies
echo "Cài đặt PyAudio dependencies..."
sudo apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    alsa-utils

# V4L2 (video4linux) cho USB camera
echo "Cài đặt v4l-utils..."
sudo apt-get install -y v4l-utils

# Git (nếu chưa có)
sudo apt-get install -y git

echo ""
echo "=== Bước 3: Tạo Python virtual environment ==="

cd /home/pi/IoT-Nha-Thong-Minh/raspberry-pi

if [ -d ".venv" ]; then
    echo -e "${YELLOW}.venv đã tồn tại, bỏ qua...${NC}"
else
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment đã được tạo${NC}"
fi

echo ""
echo "=== Bước 4: Cài đặt Python dependencies ==="

source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "=== Bước 5: Cấu hình ==="

# Copy .env.example to .env
if [ ! -f "config/.env" ]; then
    cp config/.env.example config/.env
    echo -e "${GREEN}✓ Đã tạo config/.env từ template${NC}"
    echo -e "${YELLOW}⚠ Vui lòng chỉnh sửa config/.env để cấu hình backend URL!${NC}"
else
    echo -e "${YELLOW}.env đã tồn tại, bỏ qua...${NC}"
fi

echo ""
echo "=== Bước 6: Kiểm tra hardware ==="

echo ""
echo "USB Cameras:"
v4l2-ctl --list-devices || echo -e "${RED}Không tìm thấy camera USB${NC}"

echo ""
echo "Audio Devices:"
arecord -l || echo -e "${RED}Không tìm thấy microphone${NC}"
aplay -l || echo -e "${RED}Không tìm thấy speaker${NC}"

echo ""
echo "=== Bước 7: Cấu hình permissions ==="

# Add user to gpio, audio, video groups
echo "Thêm user vào các groups cần thiết..."
sudo usermod -a -G gpio,audio,video $USER

echo ""
echo "=== Setup hoàn tất! ==="
echo ""
echo -e "${GREEN}✓ IoT Client đã sẵn sàng${NC}"
echo ""
echo "Các bước tiếp theo:"
echo "  1. Chỉnh sửa config/.env để cấu hình backend URL"
echo "  2. Kết nối relay module vào GPIO pins (xem HARDWARE.md)"
echo "  3. Cắm USB webcam vào Pi"
echo "  4. Cắm USB microphone và speaker"
echo "  5. Chạy thử: python3 src/iot_client.py"
echo "  6. Hoặc cài đặt systemd service: sudo ./scripts/install-service.sh"
echo ""
echo -e "${YELLOW}⚠ Bạn cần logout/login lại để group permissions có hiệu lực${NC}"
echo ""
