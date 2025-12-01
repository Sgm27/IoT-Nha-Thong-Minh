# Fire Detection Troubleshooting

## Quick Checklist

Run through these steps in order:

### ☑️ Step 1: Is Backend Running?

```bash
curl http://localhost:8000/smart-home/lights
```

- ✅ **Got JSON response** → Backend is running, continue
- ❌ **Connection refused** → **START BACKEND FIRST!**

**To start backend:**
```bash
docker-compose up -d backend
# Or
cd backend && uvicorn app.main:create_app --reload --host 0.0.0.0 --port 8000
```

---

### ☑️ Step 2: Check IoT Client Configuration

Your IoT client needs to connect to the backend WebSocket. Check the URL:

```bash
# On Pi, check the WebSocket URL in logs
cd ~/raspberry-pi
grep "Đang kết nối đến" /var/log/iot-client.log
```

**Should show:**
```
Đang kết nối đến ws://localhost:8000/ws/gemini
```

**If backend is on a different machine:**

Edit `/home/pi/raspberry-pi/src/iot_client.py` and change:
```python
websocket_config = WebSocketConfig(
    server_url="ws://<BACKEND_IP>:8000/ws/gemini",  # Change this!
    ...
)
```

---

### ☑️ Step 3: Verify Frames Are Being Sent

**On Raspberry Pi** (where IoT client is running):

Check if you see frame send messages:
```bash
# Watch IoT client output
tail -f /var/log/iot-client.log | grep "gửi frame"
```

**Expected every ~5 seconds:**
```
INFO - Đã gửi frame #10 (98432 bytes)
INFO - Đã gửi frame #20 (97654 bytes)
```

**If you DON'T see this:**
- Camera isn't capturing
- Callback isn't working
- Deploy updated code: `./deploy-pi-client.sh pi <PI_IP>`

---

### ☑️ Step 4: Verify Backend Receives Frames

**On Backend machine:**

```bash
# Enable DEBUG logging to see all fire detection checks
docker-compose logs -f backend | grep -E "fire|Fire|lửa|🔥"
```

**Expected (even when NO fire):**
```
DEBUG - 🔥 Không phát hiện lửa (confidence=0.5%)
DEBUG - 🔥 Không phát hiện lửa (confidence=1.2%)
```

**If you see this:** Backend IS checking for fire! Continue to Step 5.

**If you DON'T see this:**
- Backend not receiving frames
- WebSocket not connected properly
- Check backend logs for WebSocket connection: `docker-compose logs backend | grep WebSocket`

---

### ☑️ Step 5: Test with Obvious Fire

The flame might be too small or too far. Try this:

1. **Use a CANDLE** (better than lighter - larger flame)
2. Hold it **20-30cm from camera**
3. Make sure **camera is pointed at the flame**
4. **Good lighting** (not too dark, not too bright)
5. Hold for **5-10 seconds** (give it time)

**Expected in backend logs:**
```
WARNING - 🚨 FIRE DETECTED: confidence=85.3% regions=3 percentage=3.2%
```

**Then in IoT client:**
```
WARNING - 🔥 CẢNH BÁO CHÁY: Phát hiện lửa! Độ tin cậy: 85%
INFO - Buzzer 'Buzzer' beep 5 lần
```

**Then:**
- 🔔 Buzzer beeps 5 times
- 🔥 Alert appears in frontend

---

### ☑️ Step 6: Check Fire Detection Sensitivity

If you're using a flame but still no detection, check parameters:

```bash
# On backend machine
cat backend/app/utils/fire_detection.py | grep -A 10 "class FireParams"
```

**Default parameters:**
```python
lower_hsv: tuple[int, int, int] = (0, 100, 100)
upper_hsv: tuple[int, int, int] = (40, 255, 255)
min_contour_area: int = 500
fire_percentage_threshold: float = 0.02  # 2% of frame
```

**To make MORE sensitive (detect smaller fires):**

Edit `backend/app/utils/fire_detection.py`:
```python
fire_percentage_threshold: float = 0.01  # 1% instead of 2%
min_contour_area: int = 300  # Smaller fires
```

Then restart backend:
```bash
docker-compose restart backend
```

---

## Common Issues

### ❌ "No frames being sent"

**Problem:** IoT client isn't sending camera frames

**Solutions:**
1. Redeploy code: `./deploy-pi-client.sh pi <PI_IP>`
2. Restart IoT client: `sudo ./venv/bin/python3 src/iot_client.py`
3. Check camera works: `python3 scripts/test-camera.py`

---

### ❌ "Backend not receiving frames"

**Problem:** WebSocket not connected or wrong URL

**Check WebSocket connection:**
```bash
# Backend logs
docker-compose logs backend | grep -i websocket

# Should show:
# INFO - WebSocket client connected from ...
```

**If not connected:**
1. Check IoT client shows: `✓ Kết nối WebSocket thành công`
2. Check firewall allows port 8000
3. Check backend IP in IoT client config

---

### ❌ "Flame detected but no buzzer"

**Problem:** Fire detection working, but buzzer not activating

**Check:**
1. Is buzzer connected to GPIO23?
2. Test buzzer: `sudo python3 scripts/test-buzzer.py`
3. Check IoT client logs for "Buzzer beep"

---

### ❌ "False positives - detects fire when there isn't"

**Problem:** Too sensitive, detecting lights/sun

**Solution:** Make LESS sensitive:

Edit `backend/app/utils/fire_detection.py`:
```python
fire_percentage_threshold: float = 0.03  # 3% instead of 2%
min_contour_area: int = 800  # Larger fires only
```

---

## Enable Verbose Logging

To see ALL fire detection checks:

### Backend DEBUG Logging

Edit `backend/app/core/logging_config.py` or set environment:
```bash
echo "LOG_LEVEL=DEBUG" >> backend/.env
docker-compose restart backend
```

Then watch logs:
```bash
docker-compose logs -f backend | grep "🔥"
```

You should see messages for EVERY frame:
```
DEBUG - 🔥 Không phát hiện lửa (confidence=0.8%)
DEBUG - 🔥 Không phát hiện lửa (confidence=1.1%)
```

When fire appears:
```
WARNING - 🚨 FIRE DETECTED: confidence=87.5% regions=2 percentage=4.2%
```

---

## Quick Test Commands

```bash
# 1. Check backend is running
curl http://localhost:8000/smart-home/lights

# 2. Check backend logs (watch for fire detection)
docker-compose logs -f backend | grep -E "fire|Fire|🔥|lửa"

# 3. Check IoT client sending frames
ssh pi@<PI_IP>
tail -f /var/log/iot-client.log | grep "gửi frame"

# 4. Test camera
python3 scripts/test-camera.py

# 5. Test buzzer
sudo python3 scripts/test-buzzer.py

# 6. Test fire detection standalone
python3 scripts/test-fire-detection.py
```

---

## Success Indicators

Fire detection is working when you see:

1. ✅ **IoT client:** `Đã gửi frame #10`
2. ✅ **Backend:** `🔥 Không phát hiện lửa` (debug message every frame)
3. ✅ **With flame:** `🚨 FIRE DETECTED: confidence=85%`
4. ✅ **IoT client:** `🔥 CẢNH BÁO CHÁY`
5. ✅ **IoT client:** `Buzzer beep 5 lần`
6. ✅ **Physical:** Buzzer makes loud beeping sound
7. ✅ **Frontend:** Fire alert banner appears

---

## Still Not Working?

If you've checked everything and it still doesn't work:

### 1. Check backend is processing images

Add this test to backend:
```bash
# SSH to backend machine
cd backend

# Check if fire detection utils exist
ls -la app/utils/fire_detection.py

# Should exist! If not, fire detection not installed
```

### 2. Check OpenCV is installed

```bash
# On backend machine
docker-compose exec backend python3 -c "import cv2; print(cv2.__version__)"

# Should print version like: 4.8.1
```

### 3. Test fire detection manually

```bash
# On backend machine
docker-compose exec backend python3 -c "
from app.utils.fire_detection import FireDetector
detector = FireDetector()
print('Fire detector initialized successfully!')
print(f'Parameters: {detector.params}')
"
```

Should print parameters without errors.

---

## What Fire Detection Needs:

1. ✅ Backend running
2. ✅ IoT client connected to backend WebSocket
3. ✅ Camera capturing frames
4. ✅ Frames sent every ~0.5 seconds
5. ✅ OpenCV installed on backend
6. ✅ Flame visible to camera (orange/red/yellow, bright)
7. ✅ Flame at least 2% of frame size

**Remember:** Fire detection happens on the BACKEND, not the Pi!
