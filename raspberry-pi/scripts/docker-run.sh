#!/bin/bash
#
# Run IoT Client với Docker Compose
#

set -e

cd "$(dirname "$0")/.."

echo "=========================================="
echo "  Starting IoT Client Container"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f "config/.env" ]; then
    echo "⚠️  config/.env không tồn tại, tạo từ template..."
    cp config/.env.example config/.env
    echo "✓ Đã tạo config/.env"
    echo ""
    echo "⚠️  VUI LÒNG chỉnh sửa config/.env trước khi chạy!"
    echo "Đặc biệt là BACKEND_URL"
    echo ""
    read -p "Nhấn Enter để tiếp tục hoặc Ctrl+C để thoát..."
fi

# Start with docker-compose
echo "Starting container..."
docker-compose up -d

echo ""
echo "✓ Container đã được khởi động!"
echo ""
echo "Các lệnh hữu ích:"
echo "  docker-compose logs -f              # Xem logs realtime"
echo "  docker-compose ps                   # Kiểm tra status"
echo "  docker-compose stop                 # Dừng container"
echo "  docker-compose restart              # Restart container"
echo "  docker-compose down                 # Dừng và xóa container"
echo ""
