#!/bin/bash
#
# Install IoT Client systemd service
#

set -e

echo "=== Cài đặt IoT Client Service ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Vui lòng chạy script này với sudo"
    exit 1
fi

# Copy service file
echo "Copying service file..."
cp /home/pi/IoT-Nha-Thong-Minh/raspberry-pi/scripts/iot-client.service /etc/systemd/system/

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload

# Enable service
echo "Enabling service..."
systemctl enable iot-client.service

echo ""
echo "✓ Service đã được cài đặt thành công!"
echo ""
echo "Các lệnh hữu ích:"
echo "  sudo systemctl start iot-client    # Khởi động service"
echo "  sudo systemctl stop iot-client     # Dừng service"
echo "  sudo systemctl restart iot-client  # Restart service"
echo "  sudo systemctl status iot-client   # Xem trạng thái"
echo "  sudo journalctl -u iot-client -f   # Xem logs realtime"
echo ""
