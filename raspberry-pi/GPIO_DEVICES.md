# GPIO Devices Guide - LED, Buzzer, Servo

Hướng dẫn sử dụng GPIO để điều khiển LED, Buzzer, Servo trên Raspberry Pi 5.

## 🎯 Thiết bị được hỗ trợ

- ✅ **LED** - Bật/tắt đèn LED
- ✅ **Buzzer** - Phát âm thanh cảnh báo, beep
- ✅ **Servo** - Điều khiển góc quay 0-180°
- ✅ **Relay** - Bật/tắt relay module (nếu có)
- ✅ **PWM** - PWM output tùy chỉnh

## 📌 GPIO Pinout Raspberry Pi 5

### Recommended Pin Assignment

| Device Type | GPIO Pin | Physical Pin | Notes |
|-------------|----------|--------------|-------|
| LED Đỏ      | GPIO 17  | Pin 11      | Digital output |
| LED Xanh    | GPIO 27  | Pin 13      | Digital output |
| LED Vàng    | GPIO 22  | Pin 15      | Digital output |
| Buzzer      | GPIO 23  | Pin 16      | Digital output |
| Servo 1     | GPIO 18  | Pin 12      | **PWM capable** |
| Servo 2     | GPIO 13  | Pin 33      | **PWM capable** |

**PWM-capable pins** (quan trọng cho Servo):
- GPIO 12, 13 (PWM0 channel)
- GPIO 18, 19 (PWM1 channel)

## 🔌 Wiring Guide

### LED Connection

```
Raspberry Pi          LED
───────────          ─────
GPIO17  ──┐
          ├──► 330Ω Resistor ──► LED+ (Anode, chân dài)
          │                       │
          │                       ▼
          │                    LED- (Cathode, chân ngắn)
          │                       │
GND (Pin 6) ◄──────────────────┘
```

**Lưu ý:**
- Luôn dùng điện trở hạn dòng (220Ω-1kΩ)
- LED có cực tính: chân dài (+), chân ngắn (-)
- GPIO output: 3.3V (đủ cho LED)

### Buzzer Connection

**Active Buzzer** (có dao động sẵn):
```
Raspberry Pi          Buzzer
───────────          ──────
GPIO23 ───────────► Buzzer+ (hoặc I/O)
GND ──────────────► Buzzer- (hoặc GND)
```

**Passive Buzzer** (cần tín hiệu PWM):
```
Raspberry Pi          Buzzer
───────────          ──────
GPIO18 (PWM) ──────► Buzzer Signal
GND ───────────────► Buzzer GND
```

### Servo Motor Connection

**Standard Servo (SG90, MG90S):**
```
Raspberry Pi 5        Servo Motor
─────────────         ──────────
GPIO18 (PWM) ──────► Signal (Orange/Yellow wire)
5V (Pin 2) ─────────► VCC/Power (Red wire)
GND (Pin 6) ────────► GND (Brown/Black wire)
```

**Quan trọng:**
- ⚠️ Servo cần nguồn 5V riêng nếu dùng nhiều servos
- ⚠️ Dòng điện lớn có thể làm Pi restart
- ✅ Khuyến nghị: Dùng nguồn ngoài 5V-2A cho servos
- ✅ Nhớ nối chung GND giữa Pi và nguồn ngoài

## ⚙️ Configuration

### Trong `iot_client.py`:

```python
from gpio_devices import GPIODevicesController, GPIODeviceConfig, DeviceType

gpio_configs = {
    # LED
    "LED Đỏ": GPIODeviceConfig(
        gpio_pin=17,
        name="LED Đỏ",
        device_type=DeviceType.LED,
        active_high=True  # LED sáng khi GPIO HIGH
    ),

    # Buzzer
    "Buzzer": GPIODeviceConfig(
        gpio_pin=23,
        name="Buzzer Cảnh báo",
        device_type=DeviceType.BUZZER,
        active_high=True
    ),

    # Servo
    "Servo Cửa": GPIODeviceConfig(
        gpio_pin=18,  # Phải là PWM-capable pin!
        name="Servo Cửa",
        device_type=DeviceType.SERVO,
        # Servo parameters (tùy chọn, có giá trị mặc định)
        min_pulse_width=0.5/1000,   # 0.5ms cho góc 0°
        max_pulse_width=2.5/1000,   # 2.5ms cho góc 180°
        frame_width=20.0/1000       # 20ms (50Hz)
    ),
}
```

## 🎮 API Usage

### LED Control

```python
# Bật LED
gpio.led_on("LED Đỏ")

# Tắt LED
gpio.led_off("LED Đỏ")

# Toggle LED
gpio.led_toggle("LED Đỏ")

# Get state
state = gpio.get_state("LED Đỏ")  # True/False
```

### Buzzer Control

```python
# Bật buzzer
gpio.buzzer_on("Buzzer")

# Tắt buzzer
gpio.buzzer_off("Buzzer")

# Beep n lần
gpio.buzzer_beep("Buzzer", on_time=0.1, off_time=0.1, n=3)
# Beep 3 lần: 0.1s ON, 0.1s OFF, repeat 3 times
```

### Servo Control

```python
# Đặt góc cụ thể (0-180°)
gpio.servo_set_angle("Servo Cửa", 90)   # 90 độ (center)
gpio.servo_set_angle("Servo Cửa", 0)    # 0 độ (min)
gpio.servo_set_angle("Servo Cửa", 180)  # 180 độ (max)

# Hoặc dùng shortcuts
gpio.servo_center("Servo Cửa")  # 90°
gpio.servo_min("Servo Cửa")     # 0°
gpio.servo_max("Servo Cửa")     # 180°

# Get angle
angle = gpio.get_state("Servo Cửa")  # 0-180
```

## 🧪 Testing

### Test trên Raspberry Pi:

```bash
cd /home/pi/IoT-Nha-Thong-Minh/raspberry-pi

# Test với Python
python3 << 'EOF'
from src.gpio_devices import GPIODevicesController, GPIODeviceConfig, DeviceType
import time

# Config
devices = {
    "LED Test": GPIODeviceConfig(
        gpio_pin=17,
        name="LED Test",
        device_type=DeviceType.LED
    )
}

# Create controller
gpio = GPIODevicesController(devices, mock_mode=False)

# Test
gpio.led_on("LED Test")
time.sleep(1)
gpio.led_off("LED Test")

gpio.cleanup()
print("✓ Test OK!")
EOF
```

### Test Servo:

```python
from src.gpio_devices import GPIODevicesController, GPIODeviceConfig, DeviceType
import time

devices = {
    "Servo": GPIODeviceConfig(
        gpio_pin=18,
        name="Servo Test",
        device_type=DeviceType.SERVO
    )
}

gpio = GPIODevicesController(devices)

# Sweep 0 → 180 → 0
for angle in range(0, 181, 10):
    gpio.servo_set_angle("Servo", angle)
    time.sleep(0.1)

for angle in range(180, -1, -10):
    gpio.servo_set_angle("Servo", angle)
    time.sleep(0.1)

gpio.cleanup()
```

## 🔧 Integration với Backend

Devices sẽ tự động nhận lệnh từ Gemini qua WebSocket:

**Khi Gemini gọi tool `turn_on_light("LED Đỏ")`:**
```
1. Backend gửi WebSocket message:
   {"type": "smart_home_light_update", "location": "LED Đỏ", "is_on": true}

2. IoT Client nhận message → callback on_light_update()

3. GPIO controller bật LED:
   gpio.led_on("LED Đỏ")

4. LED sáng! ✨
```

## 📊 Mock Mode Testing

Test logic mà không cần hardware:

```bash
# Set MOCK_MODE=true
MOCK_MODE=true python src/iot_client.py
```

Logs sẽ hiển thị:
```
[MOCK] Khởi tạo led 'LED Đỏ' (GPIO17)
[MOCK] Khởi tạo buzzer 'Buzzer' (GPIO23)
[MOCK] Khởi tạo servo 'Servo Cửa' (GPIO18)
[MOCK] Bật led 'LED Đỏ'
[MOCK] Servo 'Servo Cửa' -> 90°
```

## 🛠️ Troubleshooting

### LED không sáng

1. **Check wiring:**
   ```bash
   # Test GPIO output
   gpio -g write 17 1  # Turn ON
   gpio -g write 17 0  # Turn OFF
   ```

2. **Check LED polarity** - Đổi chiều LED
3. **Check resistor** - Cần 220Ω-1kΩ
4. **Check voltage** - GPIO output 3.3V (đủ cho LED)

### Buzzer không kêu

1. **Active vs Passive:**
   - Active buzzer: Chỉ cần HIGH/LOW
   - Passive buzzer: Cần PWM signal

2. **Test:**
   ```python
   gpio.buzzer_on("Buzzer")
   time.sleep(1)
   gpio.buzzer_off("Buzzer")
   ```

3. **Check polarity** - Thử đổi dây +/-

### Servo không quay

1. **Check PWM pin:**
   - ⚠️ Phải dùng GPIO 12, 13, 18, 19
   - ❌ Không dùng GPIO thường (17, 22, 23...)

2. **Check power:**
   - Servo cần 5V, Pi GPIO chỉ 3.3V signal
   - Dùng nguồn ngoài 5V cho VCC

3. **Test pulse widths:**
   ```python
   # Nếu servo không quay đúng góc, điều chỉnh:
   GPIODeviceConfig(
       min_pulse_width=1.0/1000,   # Thử 1ms
       max_pulse_width=2.0/1000,   # Thử 2ms
   )
   ```

### Permission Errors

```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Logout/login lại

# Or run with sudo (not recommended)
sudo python src/iot_client.py
```

## 📚 Servo Technical Details

### Pulse Width to Angle Mapping

Standard servo (50Hz = 20ms frame):

| Angle | Pulse Width | Duty Cycle |
|-------|-------------|------------|
| 0°    | 1.0ms       | 5%         |
| 90°   | 1.5ms       | 7.5%       |
| 180°  | 2.0ms       | 10%        |

**Some servos use different ranges:**
- Budget servos: 0.5ms - 2.5ms
- High-end servos: 0.6ms - 2.4ms

**Calibration:**
```python
# Nếu servo không đạt 180° đầy đủ:
GPIODeviceConfig(
    min_pulse_width=0.5/1000,   # Extend range
    max_pulse_width=2.5/1000,   # Extend range
)
```

## 🎯 Example Projects

### 1. Smart LED Control

```python
# Bật/tắt LED từ Gemini voice:
"Bật đèn đỏ"  → LED Đỏ sáng
"Tắt đèn xanh" → LED Xanh tắt
```

### 2. Door Lock with Servo

```python
# Servo điều khiển then cửa:
gpio.servo_set_angle("Servo Cửa", 0)    # Locked
gpio.servo_set_angle("Servo Cửa", 90)   # Unlocked
```

### 3. Alarm System

```python
# Phát hiện cháy → Buzzer beep
def on_fire_alert():
    gpio.buzzer_beep("Buzzer", on_time=0.2, off_time=0.1, n=10)
    gpio.led_on("LED Đỏ")  # LED cảnh báo
```

## ✅ Checklist Setup

- [ ] Kết nối LED với resistor đúng cách
- [ ] Kết nối Buzzer (check active/passive)
- [ ] Kết nối Servo vào PWM pin (GPIO 18/13)
- [ ] Nguồn 5V riêng cho servo (khuyến nghị)
- [ ] Chung GND giữa Pi và nguồn ngoài
- [ ] Config đúng GPIO pins trong code
- [ ] Test từng device riêng trước
- [ ] Test integration với backend
- [ ] Deploy lên Pi và chạy Docker

## 🚀 Ready to Go!

Bây giờ bạn có thể:
- ✅ Điều khiển LED, Buzzer, Servo qua GPIO
- ✅ Control từ Gemini voice commands
- ✅ Test với mock mode trước khi deploy
- ✅ Easy configuration và customization

Enjoy! 🎉
