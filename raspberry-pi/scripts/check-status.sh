#!/bin/bash
# Quick status checker for IoT Smart Home

echo "=========================================="
echo "  IoT Smart Home - Status Check"
echo "=========================================="
echo ""

# Check camera
echo "📷 Camera:"
if ls /dev/video* &>/dev/null; then
    echo "  ✅ Camera devices found:"
    ls -1 /dev/video*
else
    echo "  ❌ No camera detected"
fi
echo ""

# Check backend connection
echo "🌐 Backend Connection:"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/smart-home/lights | grep -q "200"; then
    echo "  ✅ Backend is running and responding"
    echo "  📊 Current lights status:"
    curl -s http://localhost:8000/smart-home/lights | python3 -m json.tool 2>/dev/null || echo "  (JSON parse error)"
else
    echo "  ❌ Backend not responding at http://localhost:8000"
    echo "  Tip: Check if backend is running with 'docker-compose ps'"
fi
echo ""

# Check GPIO
echo "🔌 GPIO:"
if [ -d "/sys/class/gpio" ]; then
    echo "  ✅ GPIO system available"
    echo "  GPIO pins exported:"
    ls /sys/class/gpio/ | grep gpio || echo "  (none exported yet)"
else
    echo "  ❌ GPIO not available"
fi
echo ""

# Check audio devices
echo "🔊 Audio Devices:"
if command -v arecord &>/dev/null; then
    echo "  Input devices (microphone):"
    arecord -l 2>/dev/null | grep "card" || echo "  No input devices"
    echo ""
    echo "  Output devices (speaker):"
    aplay -l 2>/dev/null | grep "card" || echo "  ⚠️  No output devices (speaker disabled)"
else
    echo "  ❌ ALSA tools not installed"
fi
echo ""

# Check Python dependencies
echo "🐍 Python Environment:"
if [ -d "./venv" ]; then
    echo "  ✅ Virtual environment exists"
    if [ -f "./venv/bin/python3" ]; then
        echo "  ✅ Python binary found"
        ./venv/bin/python3 --version
    else
        echo "  ❌ Python binary not found in venv"
    fi
else
    echo "  ❌ Virtual environment not found at ./venv"
fi
echo ""

# Check if IoT client is running
echo "🤖 IoT Client Process:"
if pgrep -f "iot_client.py" > /dev/null; then
    echo "  ✅ IoT client is running"
    echo "  PID: $(pgrep -f 'iot_client.py')"
else
    echo "  ⚠️  IoT client is not running"
    echo "  Start with: sudo ./venv/bin/python3 src/iot_client.py"
fi
echo ""

echo "=========================================="
echo "  Quick Commands:"
echo "=========================================="
echo ""
echo "Test camera:"
echo "  python3 scripts/test-camera.py"
echo ""
echo "Test GPIO/LEDs:"
echo "  sudo python3 scripts/test-hardware.py"
echo ""
echo "Run IoT client:"
echo "  sudo ./venv/bin/python3 src/iot_client.py"
echo ""
echo "Control lights via API:"
echo "  curl -X POST http://localhost:8000/smart-home/lights/on \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"location\": \"phòng khách\"}'"
echo ""
