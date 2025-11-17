#!/bin/bash
#
# Uninstall IoT Client systemd service
#

set -e

echo "=== Gỡ cài đặt IoT Client Service ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Vui lòng chạy script này với sudo"
    exit 1
fi

# Stop service
echo "Stopping service..."
systemctl stop iot-client.service || true

# Disable service
echo "Disabling service..."
systemctl disable iot-client.service || true

# Remove service file
echo "Removing service file..."
rm -f /etc/systemd/system/iot-client.service

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload

echo ""
echo "✓ Service đã được gỡ cài đặt thành công!"
echo ""
