# Servo Motor Setup Guide - Raspberry Pi

Complete guide to connecting and controlling a servo motor for automatic door/window control.

## 📦 What You Need

1. **Servo Motor** (SG90, MG90S, or similar 180° servo)
2. **3 Female-to-Female jumper wires**
3. **External 5V power supply** (optional but recommended for larger servos)
4. **Something to control**: Small door, window flap, curtain, etc.

---

## 🔌 Servo Motor Wiring

Most servo motors have **3 wires**:

| Wire Color | Connection | Purpose |
|------------|------------|---------|
| **Brown/Black** | GND (Ground) | Ground/negative |
| **Red** | 5V Power | Power supply (4.8V-6V) |
| **Orange/Yellow/White** | GPIO18 | PWM signal (control) |

**Note:** Wire colors may vary by manufacturer. Check your servo's datasheet!

---

## 🔧 Connection Options

### **Option 1: Direct Connection (Small Servos Only - SG90)**

**⚠️ Only for small servos drawing < 500mA!**

```
Servo Motor          Raspberry Pi 5
━━━━━━━━━━━         ━━━━━━━━━━━━━━━━
Brown/Black  ──────→  Pin 6  (GND)
Red          ──────→  Pin 2  (5V Power)
Orange       ──────→  Pin 12 (GPIO18)
```

**Pin Layout (looking at Pi with USB ports facing down):**
```
     3.3V ●  ● 5V  ← Pin 2 (Red wire)
          ●  ● 5V
          ●  ● GND ← Pin 6 (Brown wire)
  GPIO14  ●  ● GPIO15
          ●  ● GPIO18 ← Pin 12 (Orange wire)
```

### **Option 2: External Power (Recommended for MG90S or larger)**

**For servos drawing > 500mA or multiple servos:**

```
External 5V PSU (Battery/Adapter)
    (+) ──┬──→ Servo Red (Power)
    (-)  │
         │
         └──→ Pi GND (Pin 6) ← IMPORTANT: Common ground!
         └──→ Servo Brown (Ground)

Raspberry Pi
    GPIO18 (Pin 12) ──→ Servo Orange (Signal)
```

**⚠️ CRITICAL:** Always connect **Pi GND** and **External PSU GND** together! Otherwise servo won't work.

---

## 📐 Physical Mounting Ideas

What can you control with the servo?

### **1. Small Door/Cabinet**
- Attach servo horn to door latch
- 0° = closed, 90° = open

### **2. Window Blind/Curtain**
- Attach string to servo horn
- Rotation pulls/releases string

### **3. Pet Door**
- Servo arm pushes flap open/closed

### **4. Camera Pan/Tilt**
- Mount Pi camera on servo
- Control viewing angle

### **5. Lock Mechanism**
- Servo rotates bolt/latch
- Simple automated lock

---

## ✅ Testing the Servo

### **Step 1: Test Script**

```bash
cd ~/raspberry-pi
sudo python3 scripts/test-servo.py
```

This will:
1. Move servo to 0° (fully left)
2. Move to 90° (center)
3. Move to 180° (fully right)
4. Return to center

**You should hear/see the servo moving!**

### **Step 2: Manual Test**

Create a quick test:

```bash
sudo python3 -c "
from gpiozero import Servo
from time import sleep

# Create servo on GPIO18
servo = Servo(18)

print('Moving to minimum (-1 = 0°)...')
servo.min()
sleep(2)

print('Moving to center (0 = 90°)...')
servo.mid()
sleep(2)

print('Moving to maximum (1 = 180°)...')
servo.max()
sleep(2)

print('Back to center...')
servo.mid()
sleep(1)

servo.close()
print('Done!')
"
```

---

## 🎮 Controlling the Servo

### **Method 1: Direct GPIO Control**

```python
from gpiozero import Servo

# Create servo
servo = Servo(18)

# Move to positions
servo.min()     # 0° (fully counter-clockwise)
servo.mid()     # 90° (center)
servo.max()     # 180° (fully clockwise)

# Or set specific angle
servo.value = -1    # 0°
servo.value = 0     # 90°
servo.value = 0.5   # 135°
servo.value = 1     # 180°

# Cleanup
servo.close()
```

### **Method 2: Via IoT Client (Already Configured!)**

Your servo is already configured in `iot_client.py`:
```python
"Servo Cửa": GPIODeviceConfig(
    gpio_pin=18,
    name="Servo Cửa",
    device_type=DeviceType.SERVO,
)
```

You can control it by adding commands. Let me show you how:

---

## 🔧 Add Servo Control to Your System

### **Option A: Add to Backend as a Tool**

Edit `backend/app/services/gemini_service.py` to add servo control tool:

```python
# In _create_live_config(), add to tools list:
{
    "name": "control_door",
    "description": "Mở hoặc đóng cửa bằng servo motor",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["open", "close"],
                "description": "Hành động: 'open' để mở cửa, 'close' để đóng cửa"
            }
        },
        "required": ["action"]
    }
}
```

Then add handler in `_handle_tool_calls()`:

```python
elif tool_name == "control_door":
    action = args.get("action", "")
    if action == "open":
        # Send command to open door (servo to 180°)
        await self._send_safely(websocket, {
            "type": "servo_control",
            "name": "Servo Cửa",
            "angle": 180
        })
    elif action == "close":
        # Send command to close door (servo to 0°)
        await self._send_safely(websocket, {
            "type": "servo_control",
            "name": "Servo Cửa",
            "angle": 0
        })
```

### **Option B: Quick Test Without Gemini**

Add servo callback to `iot_client.py`:

```python
# In _setup_callbacks(), add:

# WebSocket servo control
def on_servo_control(name: str, angle: float):
    """Callback for servo control"""
    logger.info(f"Điều khiển servo '{name}' đến góc {angle}°")
    self.gpio.servo_set_angle(name, angle)

self.websocket.set_servo_control_callback(on_servo_control)
```

Then in `websocket_client.py`, add:

```python
# Add to __init__:
self.on_servo_control: Optional[Callable[[str, float], None]] = None

# Add setter method:
def set_servo_control_callback(self, callback: Callable[[str, float], None]) -> None:
    """Callback for servo control (name, angle)"""
    self.on_servo_control = callback

# Add to _process_message():
elif message.get("type") == "servo_control":
    name = message.get("name", "")
    angle = message.get("angle", 90)
    if self.on_servo_control:
        self.on_servo_control(name, angle)
```

---

## 🧪 Simple Test Without Code Changes

Test servo directly via Python on Pi:

```bash
ssh pi@raspberrypi.local

# Quick servo test
sudo python3 << 'EOF'
from gpiozero import Servo
from time import sleep
import sys

servo = Servo(18)

print("Servo Door Control Test")
print("=" * 40)

try:
    while True:
        print("\nCommands:")
        print("  o - Open door (180°)")
        print("  c - Close door (0°)")
        print("  m - Middle position (90°)")
        print("  q - Quit")

        cmd = input("\nEnter command: ").lower()

        if cmd == 'o':
            print("Opening door...")
            servo.max()
        elif cmd == 'c':
            print("Closing door...")
            servo.min()
        elif cmd == 'm':
            print("Moving to middle...")
            servo.mid()
        elif cmd == 'q':
            break
        else:
            print("Invalid command!")

except KeyboardInterrupt:
    pass

servo.mid()  # Return to center
servo.close()
print("\nDone!")
EOF
```

---

## ⚠️ Troubleshooting

### **Servo jitters/shakes**
- **Cause:** Software PWM is imprecise
- **Fix:** Use hardware PWM with pigpio:
  ```bash
  sudo apt install pigpio python3-pigpio
  sudo systemctl enable pigpiod
  sudo systemctl start pigpiod
  ```

  Then in code:
  ```python
  from gpiozero import Servo
  from gpiozero.pins.pigpio import PiGPIOFactory

  factory = PiGPIOFactory()
  servo = Servo(18, pin_factory=factory)
  ```

### **Servo doesn't move**
1. Check wiring (especially power)
2. Check common ground if using external power
3. Test with multimeter: Red wire should have ~5V
4. Try different servo (it might be broken)

### **Servo moves but weak/slow**
- Not enough power! Use external 5V power supply
- Pi's 5V pin can only provide ~500mA total

### **Warning about PWMSoftwareFallback**
This is the warning you're seeing. It's harmless but servo may jitter. Install `pigpio` to fix (see above).

---

## 📊 Servo Specifications

| Servo Model | Voltage | Current | Torque | Speed |
|-------------|---------|---------|--------|-------|
| SG90 | 4.8-6V | 100-250mA | 1.8 kg⋅cm | 0.1s/60° |
| MG90S | 4.8-6V | 100-320mA | 2.2 kg⋅cm | 0.1s/60° |
| MG996R | 4.8-7.2V | 500-900mA | 11 kg⋅cm | 0.17s/60° |

**For Raspberry Pi direct connection:** Use SG90 or MG90S only!
**For larger servos:** Use external power supply

---

## 🎯 Quick Start Checklist

- [ ] Servo motor purchased (SG90 recommended)
- [ ] 3 jumper wires ready
- [ ] Wired: Brown→GND, Red→5V, Orange→GPIO18
- [ ] Tested with `scripts/test-servo.py`
- [ ] Servo moves smoothly (no jitter)
- [ ] Mounted servo to door/window/object
- [ ] Tested open/close positions

---

## 📸 Wiring Diagram

```
                    Raspberry Pi 5
              ┌─────────────────────┐
              │  ○ ○   3V3    5V ○ ○│← Red (Power)
              │  ○ ○   GPIO   5V ○ ○│
              │  ○ ○   GPIO  GND ○ ○│← Brown (Ground)
              │  ○ ○   GPIO  GPIO○ ○│
              │  ○ ○   GND  GPIO18○ ○│← Orange (Signal)
              │  ○ ○   GPIO  GPIO○ ○│
              └─────────────────────┘
                        │
                        │
              ┌─────────▼─────────┐
              │                   │
              │   Servo Motor     │
              │   (Back View)     │
              │                   │
              │  ┌───┬───┬───┐    │
              │  │Brn│Red│Org│    │
              └──┴───┴───┴───┴────┘
                 GND 5V Signal
```

---

## 💡 Project Ideas

Once your servo works, try these:

1. **Voice-controlled door**: "Mở cửa" → door opens
2. **Automated curtains**: "Đóng rèm cửa" → curtains close
3. **Smart pet feeder**: Servo releases food at scheduled times
4. **Camera gimbal**: Pan camera left/right to view different areas
5. **Automated lock**: Servo-controlled deadbolt for security

---

Need help with wiring or testing? Let me know! 🔧
