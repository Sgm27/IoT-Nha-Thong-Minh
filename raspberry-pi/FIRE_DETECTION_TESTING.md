# Fire Detection Testing Guide

Complete guide to testing the fire detection system safely and effectively.

## ⚠️ Safety First!

**IMPORTANT SAFETY RULES:**
- ✅ Test in a well-ventilated area
- ✅ Keep fire extinguisher nearby
- ✅ Use SMALL flames only (lighter, candle)
- ✅ Have water/sand ready to extinguish
- ✅ Never leave flame unattended
- ✅ Test on non-flammable surface
- ❌ DO NOT use large fires or flammable materials
- ❌ DO NOT test near smoke detectors (may trigger)

---

## Method 1: Standalone Fire Detection Test (Recommended)

Test fire detection WITHOUT running the full IoT system.

### Step 1: Deploy code to Pi
```bash
# From your Mac
./deploy-pi-client.sh pi <YOUR_PI_IP>
```

### Step 2: SSH to Raspberry Pi
```bash
ssh pi@<YOUR_PI_IP>
cd ~/raspberry-pi
```

### Step 3: Run the fire detection test script
```bash
# Real-time detection test
python3 scripts/test-fire-detection.py

# Or with preview window (if you have monitor connected)
python3 scripts/test-fire-detection.py --preview
```

### Step 4: Test with flame

**What to use:**
1. **Lighter** (easiest) ✅
2. **Small candle** ✅
3. **Match** ✅
4. **Flashlight with red/orange filter** (safe alternative)

**How to test:**
```
1. Start the script
2. Hold lighter 20-40cm from camera
3. Click lighter to create flame
4. Move flame slowly in front of camera
5. Watch terminal for detection messages
```

### Expected Output:

**No fire:**
```
✓ [14:23:45] No fire detected (Fire%: 0.1%, Regions: 0)
✓ [14:23:46] No fire detected (Fire%: 0.2%, Regions: 0)
```

**Fire detected:**
```
🔥 [14:23:47] FIRE DETECTED! Confidence: 0.85, Fire%: 3.2%, Regions: 2
   🚨 🚨 🚨 ALARM! 🚨 🚨 🚨
🔥 [14:23:48] FIRE DETECTED! Confidence: 0.92, Fire%: 4.1%, Regions: 3
   🚨 🚨 🚨 ALARM! 🚨 🚨 🚨
```

✅ **Success!** If you see fire detection messages, it works!

---

## Method 2: Full System Test (With Buzzer & Voice Alert)

Test fire detection with the complete IoT client running.

### Step 1: Start backend (if not running)
```bash
# On backend machine or Pi
docker-compose up backend
```

### Step 2: Start IoT client on Pi
```bash
ssh pi@<YOUR_PI_IP>
cd ~/raspberry-pi
sudo ./venv/bin/python3 src/iot_client.py
```

**Wait for:**
```
✓ Kết nối WebSocket thành công
Camera capture đã bắt đầu
```

### Step 3: Monitor logs in separate terminal
```bash
# Terminal 2 - Watch IoT client logs
ssh pi@<YOUR_PI_IP>
cd ~/raspberry-pi
tail -f /var/log/iot-client.log
```

### Step 4: Create flame in front of camera

Use lighter/candle as described above.

### Expected Response:

**1. IoT Client Terminal:**
```
🔥 CẢNH BÁO CHÁY: Phát hiện lửa! Độ tin cậy: 85%
INFO - Buzzer 'Buzzer' beep 5 lần
```

**2. Physical Response:**
- 🔔 **Buzzer beeps 5 times** (LOUD!)
- 🔊 **Speaker plays** (if connected): "Cảnh báo! Phát hiện lửa!"

**3. Backend Logs:**
```
INFO - Fire detected! Confidence: 0.85, Percentage: 3.2%
INFO - Sending fire alert to client
```

**4. Frontend UI:**
- 🔥 Fire alert banner appears
- ⚠️ Warning message displayed

✅ **Success!** If buzzer beeps and you see alerts, full system works!

---

## Method 3: Test with Backend API

Check what the backend sees.

### Monitor backend fire detection
```bash
# Watch backend logs
docker-compose logs -f backend | grep -i fire
```

### Trigger detection:
1. Hold flame in front of Pi camera
2. Wait 0.5-1 second (capture interval)
3. Check logs

**Expected:**
```
INFO - Processing camera frame: 1280x720
INFO - Fire detected! Confidence: 0.87, Percentage: 3.5%
INFO - Sending fire alert to WebSocket clients
```

---

## Understanding Detection Results

### Fire Detection Parameters

The system detects fire using **HSV color space** filtering:

```python
# Default parameters
lower_hsv = (0, 100, 100)    # Lower bound (Hue, Saturation, Value)
upper_hsv = (40, 255, 255)   # Upper bound
min_contour_area = 500       # Minimum fire region size
fire_threshold = 0.02        # 2% of frame must be "fire" colored
```

### What Gets Detected:

✅ **Detected as fire:**
- Lighter flame
- Candle flame
- Match flame
- Orange/red/yellow bright objects
- Very bright lights (sometimes false positive)

❌ **Not detected:**
- Smoke (no flame)
- Heat (no visual flame)
- Red objects without brightness
- Small fires far from camera

### Result Metrics:

**Confidence**: 0.0 to 1.0
- < 0.5: Low confidence (ignore)
- 0.5 - 0.7: Medium confidence
- > 0.7: High confidence ✅

**Fire Percentage**: % of frame that's fire-colored
- < 2%: Below threshold (no alert)
- 2% - 5%: Small fire
- > 5%: Large fire

**Region Count**: Number of separate fire regions
- 0: No fire
- 1-3: Typical flame
- > 5: Large fire or false positives

---

## Adjusting Sensitivity

If detection is **too sensitive** (false positives):

### Edit backend fire detection parameters:
```bash
# On backend machine
nano backend/app/utils/fire_detection.py
```

**Reduce sensitivity:**
```python
@dataclass
class FireParams:
    lower_hsv: tuple[int, int, int] = (5, 120, 120)  # More restrictive
    upper_hsv: tuple[int, int, int] = (35, 255, 255)
    min_contour_area: int = 800                      # Larger minimum
    fire_percentage_threshold: float = 0.03          # 3% instead of 2%
```

If detection is **not sensitive enough** (misses fire):

**Increase sensitivity:**
```python
@dataclass
class FireParams:
    lower_hsv: tuple[int, int, int] = (0, 80, 80)    # More permissive
    upper_hsv: tuple[int, int, int] = (45, 255, 255)
    min_contour_area: int = 300                      # Smaller minimum
    fire_percentage_threshold: float = 0.015         # 1.5% instead of 2%
```

**Restart backend** after changes:
```bash
docker-compose restart backend
```

---

## Troubleshooting

### ❌ "No fire detected" when flame is visible

**Solutions:**
1. **Move flame closer** - Camera needs to see flame clearly
2. **Ensure good lighting** - Too dark/bright affects detection
3. **Use brighter flame** - Candle better than match
4. **Adjust camera angle** - Flame should be in center of frame
5. **Lower threshold** - Edit `fire_percentage_threshold`

### ❌ False positives (detects fire when there isn't)

**Common causes:**
- Bright sunlight
- LED lights (especially red/orange)
- TV/monitor displaying fire
- Reflections

**Solutions:**
1. **Increase threshold** - Edit `fire_percentage_threshold`
2. **Restrict HSV range** - Make color detection more specific
3. **Increase min area** - Ignore small bright spots
4. **Position camera** - Avoid pointing at lights

### ❌ Buzzer doesn't beep

**Check:**
1. Buzzer connected to GPIO23?
2. IoT client running with sudo?
3. Fire alert actually triggered? (check logs)
4. Test buzzer separately: `sudo python3 scripts/test-buzzer.py`

### ❌ No alert in frontend

**Check:**
1. Backend connected to IoT client? (WebSocket logs)
2. Frontend connected to backend? (Browser console)
3. Fire detection threshold reached? (backend logs)
4. Alert cooldown active? (default 60s between alerts)

---

## Alert Cooldown

To prevent alert spam, there's a **cooldown period** between alerts.

**Default**: 60 seconds (configurable)

This means:
- Fire detected at 14:00:00 → Alert sent ✅
- Fire still detected at 14:00:30 → No alert (cooldown)
- Fire still detected at 14:01:05 → Alert sent ✅ (cooldown expired)

**To change cooldown:**
```bash
# Edit backend .env
echo "FIRE_ALERT_COOLDOWN_SECONDS=30" >> backend/.env

# Restart backend
docker-compose restart backend
```

---

## Testing Checklist

- [ ] Standalone test script detects flame (`test-fire-detection.py`)
- [ ] Backend logs show fire detection
- [ ] IoT client receives fire alert via WebSocket
- [ ] Buzzer beeps 5 times when fire detected
- [ ] Speaker plays voice warning (if connected)
- [ ] Frontend shows fire alert banner
- [ ] Alert cooldown prevents spam
- [ ] No false positives from normal lighting
- [ ] Detection sensitivity is appropriate

---

## Quick Reference

```bash
# Test fire detection standalone
python3 scripts/test-fire-detection.py

# Test with preview window (needs display)
python3 scripts/test-fire-detection.py --preview

# Single frame analysis
python3 scripts/test-fire-detection.py --mode single

# Test different camera
python3 scripts/test-fire-detection.py --device 1

# Test buzzer separately
sudo python3 scripts/test-buzzer.py

# Run full IoT client
sudo ./venv/bin/python3 src/iot_client.py

# Watch backend fire detection logs
docker-compose logs -f backend | grep -i fire

# Watch IoT client logs
tail -f /var/log/iot-client.log | grep -i fire
```

---

## Example Testing Session

```bash
# Terminal 1 - Start IoT Client
ssh pi@raspberrypi.local
cd ~/raspberry-pi
sudo ./venv/bin/python3 src/iot_client.py

# Terminal 2 - Monitor logs
ssh pi@raspberrypi.local
watch -n 0.5 'tail -20 /var/log/iot-client.log | grep -E "fire|Fire|CẢNH BÁO"'

# Terminal 3 - Backend logs
docker-compose logs -f backend | grep -i fire

# Now hold lighter in front of camera...
# Watch all 3 terminals for responses!
```

---

## Safety Reminder

**Always:**
- Use small flames only
- Keep fire extinguisher nearby
- Test in safe environment
- Never leave flame unattended
- Be prepared to extinguish quickly

**This is a REAL fire detection system - treat it seriously!**
