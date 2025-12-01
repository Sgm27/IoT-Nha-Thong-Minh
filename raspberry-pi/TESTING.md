# Testing Guide for Raspberry Pi IoT Client

This guide shows you how to verify that your camera, LEDs, and IoT client are working correctly.

## Prerequisites

Make sure you have:
- Raspberry Pi with camera plugged in
- LEDs connected to GPIO pins 17, 27, 22
- Backend server running (on Pi or another machine)
- SSH access to your Pi

## Step 1: Check Camera Hardware

### Find your camera device
```bash
ls /dev/video*
```

**Expected output:**
```
/dev/video0  /dev/video1
```

If you see devices, your camera is detected! Usually `/dev/video0` is the correct one.

### Test camera with simple capture
```bash
cd ~/raspberry-pi
python3 scripts/test-camera.py
```

**Expected output:**
```
==================================================
  Camera Test Script
==================================================

Testing camera at /dev/video0...
✅ Camera opened successfully!

Camera properties:
  Resolution: 1280x720
  FPS: 30

Capturing 5 test frames...
  ✅ Frame 1: OK (1280x720)
  ✅ Frame 2: OK (1280x720)
  ✅ Frame 3: OK (1280x720)
  ✅ Frame 4: OK (1280x720)
  ✅ Frame 5: OK (1280x720)

==================================================
✅ SUCCESS: Camera is working perfectly!
```

✅ **If you see this, your camera works!**

❌ **If it fails:**
- Check camera is plugged in securely
- Try different device: `python3 scripts/test-camera.py 1`
- Check permissions: `ls -l /dev/video0`

---

## Step 2: Test GPIO Devices

### Test LEDs
```bash
cd ~/raspberry-pi
sudo python3 scripts/test-hardware.py
```

This will:
1. Test each LED (Phòng khách, Phòng ngủ, Bếp)
2. Test buzzer
3. Test servo (if connected)

**Watch for:**
- LEDs should turn on/off
- You'll see log messages for each test

### Test Buzzer Separately
```bash
sudo python3 scripts/test-buzzer.py
```

**Expected:**
- You should hear 3 different beep patterns
- Single beep (0.5s)
- 3 beeps
- 5 rapid beeps (fire alert pattern)

✅ **If you hear beeping, buzzer works!**

---

## Step 3: Check Backend Connection

Make sure backend is running:

### If backend is on the same Raspberry Pi:
```bash
# Check if backend is running
curl http://localhost:8000/smart-home/lights

# Should return JSON with lights:
# [{"name":"phòng khách","is_on":false},...
```

### If backend is on another machine:
```bash
# Replace with your backend IP
curl http://192.168.1.100:8000/smart-home/lights
```

✅ **If you get JSON response, backend is accessible!**

---

## Step 4: Run the Full IoT Client

### Start the IoT client:
```bash
cd ~/raspberry-pi
sudo ./venv/bin/python3 src/iot_client.py
```

### What to look for in the logs:

#### ✅ **GOOD SIGNS:**

**1. GPIO Initialized:**
```
INFO - Khởi tạo led 'Phòng khách' tại GPIO17
INFO - Khởi tạo led 'Phòng ngủ' tại GPIO27
INFO - Khởi tạo led 'Bếp' tại GPIO22
```

**2. Camera Working:**
```
INFO - Camera khởi tạo thành công: 1280x720 @ 30fps
INFO - Camera capture loop bắt đầu
INFO - Camera capture đã bắt đầu
```

**3. Audio Initialized:**
```
INFO - Tìm thấy 4 audio devices
INFO - PyAudio khởi tạo thành công
INFO - Microphone recording đã bắt đầu
```

**4. WebSocket Connected:**
```
INFO - Đang kết nối đến ws://localhost:8000/ws/gemini...
INFO - ✓ Kết nối WebSocket thành công
```

**5. Audio Playback (Optional):**
```
INFO - Speaker playback đã bắt đầu
```
OR if no speaker:
```
WARNING - ⚠️  Không tìm thấy output audio device (speaker)
WARNING - ⚠️  Playback sẽ bị tắt - hệ thống vẫn hoạt động bình thường
```

#### ❌ **BAD SIGNS (Should NOT see these):**

```
ERROR - Lỗi trong capture loop: no running event loop
ERROR - Lỗi trong record loop: no running event loop
RuntimeWarning: coroutine was never awaited
```

If you see these, the fixes didn't deploy. Redeploy using `./deploy-pi-client.sh`

---

## Step 5: Test Camera Streaming to Backend

While IoT client is running, check backend logs:

### On backend machine:
```bash
# If using Docker
docker-compose logs -f backend

# If running locally
# Check terminal where uvicorn is running
```

### Look for messages like:
```
INFO - Received camera frame: 1280x720, 45KB
INFO - Fire detection: No fire detected
```

✅ **If you see these, camera frames are reaching the backend!**

---

## Step 6: Test LED Control

### Method 1: Via Backend REST API
```bash
# Turn on living room light
curl -X POST http://localhost:8000/smart-home/lights/on \
  -H "Content-Type: application/json" \
  -d '{"location": "phòng khách"}'

# Turn off
curl -X POST http://localhost:8000/smart-home/lights/off \
  -H "Content-Type: application/json" \
  -d '{"location": "phòng khách"}'
```

**Watch for:**
- LED should turn on/off
- IoT client logs should show: `INFO - Nhận lệnh: Bật 'phòng khách'`

### Method 2: Via Frontend
1. Open browser: `http://localhost:5173` (or backend IP:5173)
2. Click light switches in the UI
3. LEDs should respond immediately

### Method 3: Via Voice (Gemini)
1. In frontend, click "Bật micro"
2. Say: "Bật đèn phòng khách"
3. LED should turn on
4. Check IoT client logs for control message

---

## Step 7: Monitor Everything

### Open multiple terminal windows:

**Terminal 1 - IoT Client:**
```bash
ssh pi@raspberry.local
cd ~/raspberry-pi
sudo ./venv/bin/python3 src/iot_client.py
```

**Terminal 2 - Backend Logs:**
```bash
docker-compose logs -f backend
# or
cd backend && tail -f logs.txt
```

**Terminal 3 - Quick Tests:**
```bash
# Watch lights state
watch -n 1 'curl -s http://localhost:8000/smart-home/lights | jq'

# Test LED
curl -X POST http://localhost:8000/smart-home/lights/on \
  -H "Content-Type: application/json" \
  -d '{"location": "phòng khách"}'
```

---

## Common Issues & Solutions

### Camera not working
```bash
# Check device exists
ls -l /dev/video*

# Test with v4l2
v4l2-ctl --list-devices

# If USB camera, check USB connection
lsusb
```

### LEDs not responding
```bash
# Check GPIO pins
sudo cat /sys/kernel/debug/gpio

# Test LED manually
sudo python3 -c "
from gpiozero import LED
led = LED(17)
led.on()
input('Press Enter to turn off...')
led.off()
"
```

### WebSocket connection failed
```bash
# Check backend is running
curl http://localhost:8000/smart-home/lights

# Check network connectivity
ping localhost

# If backend on different machine
ping <backend-ip>
```

### "Event loop" errors
This means the fixes didn't deploy. Deploy again:
```bash
# From your development machine
./deploy-pi-client.sh pi raspberry.local
```

---

## Success Checklist

- [ ] Camera test passes (`scripts/test-camera.py`)
- [ ] GPIO test passes (`scripts/test-hardware.py`)
- [ ] Backend API responds (`curl http://localhost:8000/smart-home/lights`)
- [ ] IoT client starts without errors
- [ ] WebSocket connects successfully
- [ ] Camera frames appear in backend logs
- [ ] LED control works (via API or frontend)
- [ ] No "event loop" errors in logs

If all checked, **everything is working!** ✅

---

## Quick Reference

```bash
# Deploy code from Mac to Pi
./deploy-pi-client.sh pi raspberry.local

# On Raspberry Pi:

# Test camera
python3 scripts/test-camera.py

# Test GPIO
sudo python3 scripts/test-hardware.py

# Run IoT client
sudo ./venv/bin/python3 src/iot_client.py

# Test LED control
curl -X POST http://localhost:8000/smart-home/lights/on \
  -H "Content-Type: application/json" \
  -d '{"location": "phòng khách"}'

# View backend logs
docker-compose logs -f backend
```
