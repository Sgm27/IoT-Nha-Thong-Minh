#!/bin/bash
# Quick fire detection status checker

echo "=========================================="
echo "  Fire Detection Status Check"
echo "=========================================="
echo ""

# Check 1: Backend running?
echo "1️⃣  Checking backend..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/smart-home/lights | grep -q "200"; then
    echo "   ✅ Backend is running at http://localhost:8000"
else
    echo "   ❌ Backend NOT running!"
    echo "   ⚠️  FIRE DETECTION WILL NOT WORK WITHOUT BACKEND!"
    echo ""
    echo "   Start backend with:"
    echo "   docker-compose up -d backend"
    echo ""
    exit 1
fi

# Check 2: Backend logs for fire detection
echo ""
echo "2️⃣  Checking backend fire detection..."
echo "   Looking for recent fire detection logs..."
echo ""

if command -v docker-compose &>/dev/null; then
    echo "   Last 10 fire detection log entries:"
    docker-compose logs --tail=100 backend 2>/dev/null | grep -E "fire|Fire|lửa|🔥" | tail -10

    if [ $? -eq 0 ]; then
        echo ""
        echo "   ✅ Fire detection IS running in backend"
        echo "   If you see 'Không phát hiện lửa' → Backend is checking frames!"
    else
        echo "   ⚠️  No fire detection logs found"
        echo "   This could mean:"
        echo "   - No camera frames received yet"
        echo "   - Fire detection not enabled"
        echo "   - IoT client not connected"
    fi
else
    echo "   ⚠️  docker-compose not found, skipping backend log check"
fi

# Check 3: Environment
echo ""
echo "3️⃣  Fire Detection Configuration"
echo "   Default parameters:"
echo "   - Fire threshold: 2% of frame"
echo "   - HSV range: (0,100,100) to (40,255,255)"
echo "   - Min contour: 500 pixels"
echo "   - Alert cooldown: 60 seconds"
echo ""

# Instructions
echo ""
echo "=========================================="
echo "  How to Test Fire Detection"
echo "=========================================="
echo ""
echo "1. Make sure backend is running (checked ✅ above)"
echo ""
echo "2. On Raspberry Pi, run IoT client:"
echo "   ssh pi@<PI_IP>"
echo "   cd ~/raspberry-pi"
echo "   sudo ./venv/bin/python3 src/iot_client.py"
echo ""
echo "3. Wait for 'WebSocket connected' message"
echo ""
echo "4. Watch backend logs (in another terminal):"
echo "   docker-compose logs -f backend | grep -E '🔥|fire|Fire'"
echo ""
echo "5. Hold CANDLE or LIGHTER in front of Pi camera (20-30cm)"
echo ""
echo "6. Expected:"
echo "   Backend: 🚨 FIRE DETECTED: confidence=85% ..."
echo "   Pi: 🔥 CẢNH BÁO CHÁY ..."
echo "   Pi: Buzzer beep 5 lần"
echo "   Physical: LOUD BEEPING from buzzer"
echo ""
echo "=========================================="
echo "  Troubleshooting"
echo "=========================================="
echo ""
echo "If no detection:"
echo ""
echo "• Flame too small? → Use candle instead of lighter"
echo "• Flame too far? → Move closer (20-30cm)"
echo "• Too dark/bright? → Adjust lighting"
echo "• No frames? → Check: docker-compose logs backend | grep camera"
echo ""
echo "For detailed troubleshooting:"
echo "  cat raspberry-pi/FIRE_DETECTION_TROUBLESHOOTING.md"
echo ""
