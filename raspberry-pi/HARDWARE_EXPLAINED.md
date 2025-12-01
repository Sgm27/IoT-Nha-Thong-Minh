# Hardware Components Explained

This document explains what each hardware component does in the IoT Smart Home system.

## 🔌 GPIO Devices (Connected to Raspberry Pi)

### 💡 LEDs (3x) - Room Lights
**Purpose**: Control room lighting through Gemini voice commands

**GPIO Pins**:
- GPIO17 → Phòng khách (Living room)
- GPIO27 → Phòng ngủ (Bedroom)
- GPIO22 → Bếp (Kitchen)

**How to control**:
- Voice: "Bật đèn phòng khách" (Turn on living room light)
- Frontend UI: Click light switches
- REST API: POST to `/smart-home/lights/on` or `/off`

**When they activate**:
- When you ask Gemini to control lights
- When you toggle switches in the web interface
- When backend sends control commands

---

### 🔔 Buzzer (1x) - Fire Alert Alarm
**Purpose**: LOUD beeping sound for fire detection warnings

**GPIO Pin**: GPIO23

**When it activates**:
- 🔥 **Fire detected by camera** → 5 rapid beeps (BEEP-BEEP-BEEP-BEEP-BEEP)
- Each beep: 0.2s on, 0.1s off
- Automatic activation when fire detection confidence > threshold

**Pattern**:
```
Fire Detected → Backend analyzes camera frame → Fire alert sent →
→ Buzzer beeps 5 times + Voice warning through speaker
```

**Why it's important**:
- Even if speaker is not connected, you'll hear the buzzer
- Loud enough to wake you up or alert you from another room
- Physical alert that can't be missed

**Test it**:
```bash
sudo python3 scripts/test-buzzer.py
```

---

### 🎚️ Servo (1x) - Door/Window Control (Optional)
**Purpose**: Open/close door or window automatically

**GPIO Pin**: GPIO18 (Hardware PWM support)

**Angle control**: 0° to 180°
- 0° = Fully closed
- 90° = Half open
- 180° = Fully open

**When it activates**:
- Can be controlled via Gemini commands (if you add the tool)
- Currently configured but not used in default setup

**Example use cases**:
- "Mở cửa" (Open door)
- "Đóng cửa sổ" (Close window)
- Automatic door opening when you arrive home

---

## 📷 Camera - Vision Input

### USB Webcam
**Purpose**:
1. **Fire detection** - Analyzes frames for fire/flames using OpenCV
2. **Visual context for Gemini** - Sends images to Gemini for visual understanding

**Device**: `/dev/video0` (usually)

**Specifications**:
- Resolution: 1280x720 (downscaled to 720px max)
- Frame rate: 30 FPS capture, ~2 FPS sent to backend
- Compression: JPEG, quality 75%

**How it works**:
```
Camera → Capture frame every 0.5s → JPEG compress →
→ Send to backend → Fire detection + Gemini analysis
```

**Fire Detection Process**:
1. Camera captures frame
2. Backend receives JPEG image
3. OpenCV analyzes HSV color space for flames
4. If fire detected → Alert sent to IoT client
5. Buzzer beeps + Voice warning plays

**Test it**:
```bash
python3 scripts/test-camera.py
```

---

## 🎤 Microphone - Voice Input

### USB Microphone
**Purpose**: Capture your voice for Gemini conversation

**Audio specs**:
- Sample rate: 16kHz (required by Gemini)
- Format: PCM16 mono
- Chunk size: 100ms per transmission

**How it works**:
```
Your voice → Microphone → Audio capture →
→ Resample to 16kHz → WebSocket → Gemini → Response
```

**When it's active**:
- Continuously recording when IoT client is running
- Audio only sent to Gemini when WebSocket is connected

**Test it**:
```bash
arecord -l  # List recording devices
arecord -d 5 test.wav  # Record 5 seconds
aplay test.wav  # Play back
```

---

## 🔊 Speaker - Audio Output (Optional)

### USB Speaker or 3.5mm Jack
**Purpose**: Play Gemini's voice responses and fire alerts

**Audio specs**:
- Sample rate: 24kHz (Gemini output)
- Format: PCM16
- Playback queue managed to prevent overlap

**What it plays**:
1. **Gemini voice responses** - AI assistant talking back to you
2. **Fire alert warnings** - "Cảnh báo! Phát hiện lửa!" (Warning! Fire detected!)
3. **System notifications** - Status updates

**If no speaker connected**:
- System still works normally
- You just won't hear voice responses
- Buzzer still works for fire alerts
- Visual feedback in logs and frontend UI

**Test it**:
```bash
aplay -l  # List playback devices
speaker-test -t wav -c 1  # Test speaker
```

---

## 🔄 How Everything Works Together

### Normal Operation:
```
1. Microphone captures your voice → Gemini
2. Gemini processes command
3. If light control → LED turns on/off
4. Gemini responds → Speaker plays voice
```

### Fire Detection:
```
1. Camera captures frames continuously
2. Backend analyzes each frame with OpenCV
3. Fire detected (HSV color + contour analysis)
4. Alert sent to IoT client via WebSocket
5. Buzzer beeps 5 times (LOUD)
6. Speaker plays voice warning (if connected)
7. Frontend shows fire alert message
```

### Voice-Controlled Lights:
```
You: "Bật đèn phòng khách"
→ Microphone → Gemini → Understands intent
→ Backend calls turn_on_light tool
→ WebSocket message to IoT client
→ GPIO17 activated → LED turns on
→ Gemini: "Đã bật đèn phòng khách"
→ Speaker plays response
```

---

## 📊 Hardware Requirements Summary

| Component | Quantity | GPIO/Device | Required? | Purpose |
|-----------|----------|-------------|-----------|---------|
| LED | 3 | GPIO 17, 27, 22 | Yes | Room lights |
| Buzzer | 1 | GPIO 23 | **Highly Recommended** | Fire alerts |
| Servo | 1 | GPIO 18 | Optional | Door control |
| USB Camera | 1 | /dev/video0 | Yes | Fire detection + Vision |
| USB Microphone | 1 | ALSA device | Yes | Voice input |
| Speaker | 1 | ALSA device | Optional | Voice output |

---

## 🎯 Quick Summary

**Buzzer = Fire alarm**
- Only beeps when fire is detected
- 5 rapid beeps
- Cannot be controlled manually (safety feature)
- Always active when IoT client is running

**LEDs = Room lights**
- Controlled by voice or UI
- Always on/off based on commands

**Camera = Eyes of the system**
- Watches for fire continuously
- Provides visual context to Gemini

**Microphone = Your voice**
- Listens for commands

**Speaker = Gemini's voice (optional)**
- Responds to you
- Plays fire warnings

---

## 🧪 Test All Components

```bash
cd ~/raspberry-pi

# 1. Test camera
python3 scripts/test-camera.py

# 2. Test buzzer
sudo python3 scripts/test-buzzer.py

# 3. Test all GPIO devices (LEDs, buzzer, servo)
sudo python3 scripts/test-hardware.py

# 4. Check system status
./scripts/check-status.sh

# 5. Run full system
sudo ./venv/bin/python3 src/iot_client.py
```

---

## ⚠️ Safety Notes

**Buzzer**:
- Designed to be LOUD for safety
- Will activate automatically during fire detection
- Cannot be disabled (safety feature)
- If too loud, you can adjust beep duration in code

**Fire Detection**:
- Runs continuously on all camera frames
- Threshold-based: configurable sensitivity
- Cooldown period prevents spam (60 seconds default)
- False positives possible with bright lights/candles

**Electrical Safety**:
- Always use proper resistors with LEDs
- Buzzer typically 5V active
- Never exceed GPIO pin current limits (16mA)
- Use relay modules for AC devices
