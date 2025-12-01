# DC Motor Integration Guide

How to integrate your DC motor into the existing IoT Smart Home system.

---

## 🎯 Overview

After wiring and testing your DC motor with the test script, follow these steps to integrate it into your voice-controlled smart home system.

---

## Step 1: Check GPIO Device Types

First, check if `DeviceType.MOTOR` exists in your code:

```bash
# SSH to Pi
ssh pi@raspberrypi.local

# Check gpio_devices.py
cd ~/raspberry-pi/src
grep -n "MOTOR" gpio_devices.py
```

**If you see `MOTOR` in the DeviceType enum:** Great! Skip to Step 2.

**If you DON'T see `MOTOR`:** You need to add it to `gpio_devices.py`

---

## Step 2: Modify `iot_client.py` Configuration

Edit `raspberry-pi/src/iot_client.py` in the `main()` function:

**Find this section (around line 280-285):**

```python
# Servo (nếu có)
"Servo Cửa": GPIODeviceConfig(
    gpio_pin=18,  # GPIO 18 hỗ trợ hardware PWM
    name="Servo Cửa",
    device_type=DeviceType.SERVO,
),
```

**Replace with this:**

```python
# DC Motor - Fan/Pump
"Quạt": GPIODeviceConfig(
    gpio_pin=(23, 24, 18),  # (IN1, IN2, ENA) for L298N
    name="Quạt",
    device_type=DeviceType.MOTOR,  # or SERVO if MOTOR not available
),
```

**Note:** The gpio_pin now takes a tuple of 3 pins: `(forward_pin, backward_pin, enable_pin)`

---

## Step 3: Add Motor Control Callback

In `iot_client.py`, find the `_setup_callbacks()` method (around line 117).

**Add this new callback AFTER the fire alert callback:**

```python
# WebSocket motor control
def on_motor_control(name: str, action: str, speed: float = 1.0):
    """Callback for motor control"""
    logger.info(f"Điều khiển motor '{name}': {action} (tốc độ {speed*100}%)")

    # Find motor in GPIO configs
    if name not in self.gpio.devices:
        logger.warning(f"Motor '{name}' không tồn tại")
        return

    device = self.gpio.devices[name]

    # Check if device is a motor (gpiozero.Motor)
    from gpiozero import Motor
    if not isinstance(device, Motor):
        logger.warning(f"Device '{name}' không phải motor")
        return

    # Control motor based on action
    if action == "forward" or action == "on":
        device.forward(speed=speed)
        logger.info(f"✓ Motor '{name}' chạy tiến (tốc độ {speed*100}%)")

    elif action == "backward" or action == "reverse":
        device.backward(speed=speed)
        logger.info(f"✓ Motor '{name}' chạy lùi (tốc độ {speed*100}%)")

    elif action == "stop" or action == "off":
        device.stop()
        logger.info(f"✓ Motor '{name}' đã dừng")

    else:
        logger.warning(f"Hành động không hợp lệ: {action}")

self.websocket.set_motor_control_callback(on_motor_control)
```

---

## Step 4: Add WebSocket Motor Control

Edit `raspberry-pi/src/websocket_client.py`:

**In the `__init__` method, add:**

```python
self.on_motor_control: Optional[Callable[[str, str, float], None]] = None
```

**Add this setter method:**

```python
def set_motor_control_callback(
    self,
    callback: Callable[[str, str, float], None]
) -> None:
    """Callback for motor control (name, action, speed)"""
    self.on_motor_control = callback
```

**In the `_process_message()` method, add this case:**

```python
elif message.get("type") == "motor_control":
    name = message.get("name", "")
    action = message.get("action", "")
    speed = message.get("speed", 1.0)
    if self.on_motor_control:
        self.on_motor_control(name, action, speed)
```

---

## Step 5: Backend Integration - Add Gemini Tool

Edit `backend/app/services/gemini_service.py`:

**In the `_create_live_config()` method, add this tool to the tools list:**

```python
{
    "name": "control_motor",
    "description": "Điều khiển động cơ DC (quạt, máy bơm, v.v.)",
    "parameters": {
        "type": "object",
        "properties": {
            "device": {
                "type": "string",
                "description": "Tên thiết bị motor: 'Quạt'"
            },
            "action": {
                "type": "string",
                "enum": ["on", "off", "forward", "backward", "stop"],
                "description": "Hành động: 'on' (bật), 'off' (tắt), 'forward' (tiến), 'backward' (lùi), 'stop' (dừng)"
            },
            "speed": {
                "type": "number",
                "description": "Tốc độ từ 0.0 đến 1.0 (0% đến 100%)",
                "minimum": 0.0,
                "maximum": 1.0
            }
        },
        "required": ["device", "action"]
    }
}
```

**In the `_handle_tool_calls()` method, add this handler:**

```python
elif tool_name == "control_motor":
    device = args.get("device", "")
    action = args.get("action", "")
    speed = args.get("speed", 1.0)

    logger.info(f"🎮 Gemini điều khiển motor: {device} → {action} (tốc độ {speed*100}%)")

    # Send motor control message to Pi via WebSocket
    await self._send_safely(websocket, {
        "type": "motor_control",
        "name": device,
        "action": action,
        "speed": speed
    })
```

**Update the `SYSTEM_INSTRUCTION` to include motor control:**

Find the system instruction string and add motor information:

```python
SYSTEM_INSTRUCTION = """
...
Các thiết bị bạn có thể điều khiển:
- Đèn: Phòng khách, Phòng ngủ, Bếp
- Cảnh báo: Buzzer
- Động cơ: Quạt (có thể bật/tắt và điều chỉnh tốc độ)

Lệnh điều khiển motor:
- "Bật quạt" → control_motor(device="Quạt", action="on", speed=1.0)
- "Tắt quạt" → control_motor(device="Quạt", action="off")
- "Chạy quạt chậm" → control_motor(device="Quạt", action="on", speed=0.3)
- "Quạt tốc độ cao" → control_motor(device="Quạt", action="on", speed=1.0)
...
"""
```

---

## Step 6: Test Voice Control

After making these changes:

**1. Rebuild and restart:**

```bash
# From project root on your Mac/PC
cd /Users/h3nr1.d14z/Projects/HieuLD/IoT-Nha-Thong-Minh

# Rebuild Docker containers
docker-compose down
docker-compose up --build
```

**2. Deploy to Raspberry Pi:**

```bash
# Copy updated files to Pi
./deploy-all-to-pi.sh
```

**3. Restart IoT client on Pi:**

```bash
ssh pi@raspberrypi.local

# Stop old process
sudo pkill -f iot_client.py

# Start new process
cd ~/raspberry-pi
sudo python3 src/iot_client.py
```

**4. Test voice commands:**

Try these voice commands through the web interface:

- "Bật quạt" (Turn on fan)
- "Tắt quạt" (Turn off fan)
- "Quạt chạy chậm" (Fan run slow)
- "Quạt tốc độ cao" (Fan high speed)
- "Dừng quạt" (Stop fan)

---

## 🎮 Direct Testing (Without Voice)

You can also test directly via WebSocket messages:

**Using browser console on frontend (http://localhost:5173):**

```javascript
// Get the WebSocket connection from React hook
// (You'll need to expose this in useGeminiRealtime.ts for testing)

// Send motor control message
ws.send(JSON.stringify({
    type: "motor_control",
    name: "Quạt",
    action: "on",
    speed: 0.5  // 50% speed
}));

// Stop motor
ws.send(JSON.stringify({
    type: "motor_control",
    name: "Quạt",
    action: "stop"
}));
```

---

## 🔧 GPIO Device Implementation (If MOTOR Type Missing)

If `DeviceType.MOTOR` doesn't exist, you need to add it to `gpio_devices.py`:

**1. Find the `DeviceType` enum:**

```python
class DeviceType(str, Enum):
    LED = "led"
    RELAY = "relay"
    BUZZER = "buzzer"
    SERVO = "servo"
    MOTOR = "motor"  # ← Add this line
```

**2. Update the `_create_device()` method in `GPIODevicesController`:**

```python
def _create_device(self, config: GPIODeviceConfig):
    """Create GPIO device based on config"""

    if config.device_type == DeviceType.MOTOR:
        # Motor requires 3 pins: (forward, backward, enable)
        if isinstance(config.gpio_pin, tuple) and len(config.gpio_pin) == 3:
            forward_pin, backward_pin, enable_pin = config.gpio_pin
            return Motor(
                forward=forward_pin,
                backward=backward_pin,
                enable=enable_pin,
                pin_factory=self.pin_factory
            )
        else:
            logger.error(f"Motor '{config.name}' cần 3 pins (forward, backward, enable)")
            return None

    elif config.device_type == DeviceType.SERVO:
        # Existing servo code...
        pass

    # ... rest of device types ...
```

**3. Add Motor import:**

```python
from gpiozero import LED, OutputDevice, Servo, Motor, PWMOutputDevice
```

**4. Add motor control methods to `GPIODevicesController`:**

```python
def motor_forward(self, name: str, speed: float = 1.0) -> bool:
    """Run motor forward at given speed"""
    device = self.devices.get(name)
    if device and isinstance(device, Motor):
        device.forward(speed=speed)
        return True
    return False

def motor_backward(self, name: str, speed: float = 1.0) -> bool:
    """Run motor backward at given speed"""
    device = self.devices.get(name)
    if device and isinstance(device, Motor):
        device.backward(speed=speed)
        return True
    return False

def motor_stop(self, name: str) -> bool:
    """Stop motor"""
    device = self.devices.get(name)
    if device and isinstance(device, Motor):
        device.stop()
        return True
    return False
```

---

## 📋 Integration Checklist

- [ ] Wired L298N to Pi (see MOTOR_WIRING_CHECKLIST.md)
- [ ] Tested motor with `test-dc-motor.py` (motor spins)
- [ ] Added `DeviceType.MOTOR` to `gpio_devices.py` (if needed)
- [ ] Updated motor creation in `GPIODevicesController`
- [ ] Modified `iot_client.py` config to use motor instead of servo
- [ ] Added motor control callback in `iot_client.py`
- [ ] Added WebSocket motor control in `websocket_client.py`
- [ ] Added Gemini tool in `gemini_service.py`
- [ ] Updated system instruction
- [ ] Rebuilt Docker containers
- [ ] Deployed to Pi
- [ ] Tested voice control

---

## 🎯 Voice Command Examples

Once integrated, these commands will work:

**Vietnamese (Primary):**
- "Bật quạt" → Fan on full speed
- "Tắt quạt" → Fan off
- "Quạt chạy chậm" → Fan 30% speed
- "Quạt mạnh hơn" → Fan 80% speed
- "Dừng quạt" → Fan stop

**English (if configured):**
- "Turn on the fan"
- "Turn off the fan"
- "Run fan slowly"
- "Fan high speed"
- "Stop the fan"

---

## 🛠️ Troubleshooting

### Motor doesn't respond to voice commands

**Check logs:**
```bash
# Backend logs
docker-compose logs -f backend

# Pi logs
ssh pi@raspberrypi.local
tail -f /var/log/iot-client.log
```

**Look for:**
- "🎮 Gemini điều khiển motor" in backend logs
- "Điều khiển motor" in Pi logs
- WebSocket connection errors

### Motor runs but in wrong direction

Swap the motor wires at L298N OUT1/OUT2, or use `action="backward"` instead of `action="forward"`

### Motor speed doesn't change

Make sure `speed` parameter is being passed correctly (0.0-1.0 range)

---

## 📊 Architecture Overview

```
Voice Command
    ↓
Gemini API (backend)
    ↓
control_motor() tool call
    ↓
WebSocket message {"type": "motor_control"}
    ↓
Raspberry Pi websocket_client.py
    ↓
on_motor_control() callback
    ↓
GPIO Motor object
    ↓
L298N Driver
    ↓
DC Motor spins! ⚙️
```

---

## 🚀 Advanced Features

Once basic control works, you can add:

1. **Speed presets:**
   - Low: 0.3 (30%)
   - Medium: 0.6 (60%)
   - High: 1.0 (100%)

2. **Auto-control based on temperature:**
   - Add temperature sensor
   - Auto-turn on fan when hot

3. **Fire response:**
   - Auto-turn on fan when fire detected (to vent smoke)
   - Or auto-turn OFF if fire is electrical

4. **Timer control:**
   - "Turn on fan for 5 minutes"
   - Auto-shutoff after delay

5. **Frontend UI:**
   - Add motor control card in React app
   - Speed slider (0-100%)
   - Direction buttons (Forward/Backward/Stop)

---

Need help? Check the full setup guide: **DC_MOTOR_SETUP.md**
