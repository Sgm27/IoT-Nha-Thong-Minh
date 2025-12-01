# Test Hardware - LED và Buzzer

Hướng dẫn test LED, Buzzer, Servo để kiểm tra đã nối đúng chưa.

## 🧪 Cách 1: Test nhanh (Interactive Menu)

```bash
# SSH vào Raspberry Pi
ssh pi@raspberry.local

cd /home/pi/IoT-Nha-Thong-Minh/raspberry-pi

# Chạy test script
./scripts/test-simple.sh
```

**Menu sẽ hiện ra:**
```
======================================
  Simple Hardware Test
======================================

Chọn device cần test:
  1) LED Đỏ (GPIO17)
  2) LED Xanh (GPIO27)
  3) LED Vàng (GPIO22)
  4) Buzzer (GPIO23)
  5) Servo (GPIO18)
  6) Test tất cả
  0) Exit

Nhập số (0-6):
```

Nhập số → LED/Buzzer sẽ hoạt động → Quan sát xem có hoạt động không!

## 🔬 Cách 2: Test tất cả devices (Full Test)

```bash
cd /home/pi/IoT-Nha-Thong-Minh/raspberry-pi

# Activate venv (nếu dùng venv)
source venv/bin/activate

# Chạy full test
python3 scripts/test-hardware.py
```

**Kết quả:**
```
🧪 Hardware Test Script
==================================================

This script will test all connected hardware:
  - LEDs will blink 3 times
  - Buzzer will beep 3 times
  - Servo will sweep through angles

Press ENTER to start testing...

==================================================
  Testing LEDs
==================================================

🔴 Testing LED Đỏ (GPIO17)...
   LED should BLINK 3 times...
   Blink 1/3: ON → OFF
   Blink 2/3: ON → OFF
   Blink 3/3: ON → OFF
✅ LED Đỏ test completed!

... (tương tự cho LED Xanh, Vàng, Buzzer, Servo)

==================================================
  Test Summary
==================================================
  LED Đỏ               ✅ PASS
  LED Xanh             ✅ PASS
  LED Vàng             ✅ PASS
  Buzzer               ✅ PASS
  Servo Cửa            ✅ PASS

Total: 5/5 tests passed

🎉 All tests PASSED! Hardware is working correctly!
```

## 🔧 Cách 3: Test thủ công từng device

### Test LED bằng lệnh đơn giản:

```bash
# Test LED Đỏ (GPIO17)
python3 << 'EOF'
from gpiozero import LED
import time

led = LED(17)  # GPIO17

# Blink 5 lần
for i in range(5):
    led.on()
    print("LED ON")
    time.sleep(0.5)
    led.off()
    print("LED OFF")
    time.sleep(0.5)

led.close()
EOF
```

**Thay đổi GPIO pin:**
- LED Đỏ: `LED(17)`
- LED Xanh: `LED(27)`
- LED Vàng: `LED(22)`

### Test Buzzer:

```bash
# Test Buzzer (GPIO23)
python3 << 'EOF'
from gpiozero import Buzzer
import time

buzzer = Buzzer(23)

# Beep 3 lần
buzzer.beep(on_time=0.2, off_time=0.2, n=3, background=False)

buzzer.close()
EOF
```

### Test Servo:

```bash
# Test Servo (GPIO18)
python3 << 'EOF'
from gpiozero import Servo
import time

servo = Servo(18)

# Quay từ 0° → 180°
print("Moving to 0°")
servo.min()
time.sleep(1)

print("Moving to 90°")
servo.mid()
time.sleep(1)

print("Moving to 180°")
servo.max()
time.sleep(1)

servo.close()
EOF
```

## 🐛 Troubleshooting

### LED không sáng:

**Nguyên nhân có thể:**
1. ❌ Cắm ngược polarity
2. ❌ Thiếu điện trở 330Ω
3. ❌ LED hỏng
4. ❌ GPIO pin sai

**Cách fix:**

```bash
# Bước 1: Kiểm tra LED polarity
# Chân DÀI (+) = Anode → Nối với điện trở → GPIO
# Chân NGẮN (-) = Cathode → Nối với GND

# Bước 2: Đổi chiều LED thử
# Nếu sáng → OK!

# Bước 3: Test LED trực tiếp (không qua code)
# Tắt Pi → Rút dây LED khỏi GPIO17
# Cắm dây đó vào Pin 1 (3.3V) trực tiếp
# Bật Pi → LED sáng = LED OK, wiring đúng

# Bước 4: Kiểm tra điện trở
# Phải có 330Ω giữa GPIO và LED+
# Màu: Cam-Cam-Nâu

# Bước 5: Kiểm tra GPIO pin
gpio readall
# Tìm GPIO17, kiểm tra có active không
```

### Buzzer không kêu:

**Nguyên nhân:**
1. ❌ Cắm ngược +/-
2. ❌ Passive buzzer (cần PWM) thay vì active buzzer
3. ❌ Buzzer hỏng

**Cách fix:**

```bash
# Bước 1: Đổi chiều buzzer
# Thử cắm ngược +/- và test lại

# Bước 2: Kiểm tra loại buzzer
# Active buzzer: Có oscillator sẵn, chỉ cần HIGH/LOW
# Passive buzzer: Cần PWM signal

# Nếu là passive buzzer, phải dùng PWM:
python3 << 'EOF'
from gpiozero import TonalBuzzer
from gpiozero.tones import Tone
import time

buzzer = TonalBuzzer(23)
buzzer.play(Tone("A4"))
time.sleep(1)
buzzer.stop()
EOF

# Bước 3: Test buzzer trực tiếp
# Nối buzzer+ vào 3.3V pin
# Nối buzzer- vào GND
# Nếu kêu → Buzzer OK
```

### Servo không quay:

**Nguyên nhân:**
1. ❌ Không phải PWM pin
2. ❌ Thiếu nguồn 5V
3. ❌ Servo hỏng

**Cách fix:**

```bash
# Bước 1: Kiểm tra PWM pin
# Servo PHẢI dùng GPIO 18, 13, 12, hoặc 19 (PWM-capable)
# Không dùng GPIO thường (17, 22, 23...)

# Bước 2: Kiểm tra nguồn
# Servo cần 5V, không phải 3.3V
# Kiểm tra dây ĐỎ của servo nối vào Pin 2 hoặc Pin 4 (5V)

# Bước 3: Kiểm tra dòng điện
# 1 servo OK, nhưng 2+ servo cần nguồn ngoài
# Pi có thể restart nếu servo hút quá nhiều điện

# Bước 4: Test servo với pulse width khác
python3 << 'EOF'
from gpiozero import Servo
from gpiozero.pins.lgpio import LGPIOFactory
import time

factory = LGPIOFactory()
servo = Servo(18, pin_factory=factory, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000)

servo.min()
time.sleep(1)
servo.max()
time.sleep(1)
servo.mid()

servo.close()
EOF
```

## 📊 Kiểm tra GPIO status

```bash
# Xem tất cả GPIO pins
gpio readall

# Output:
# +-----+-----+---------+------+---+---Pi 5---+---+------+---------+-----+-----+
#  | BCM | wPi |   Name  | Mode | V | Physical | V | Mode | Name    | wPi | BCM |
#  +-----+-----+---------+------+---+----++----+---+------+---------+-----+-----+
#  |     |     |    3.3v |      |   |  1 || 2  |   |      | 5v      |     |     |
#  |   2 |   8 |   SDA.1 |   IN | 1 |  3 || 4  |   |      | 5v      |     |     |
#  |  17 |   0 |  GPIO17 |  OUT | 0 | 11 || 12 |   | ALT0 | GPIO18  |  1 | 18  |
#  ...
```

## ✅ Expected Results

### LED Test:
- LED sáng trong 0.5 giây
- LED tắt trong 0.5 giây
- Lặp lại 5 lần
- Brightness ổn định (không nhấp nháy)

### Buzzer Test:
- Âm thanh "beep" rõ ràng
- Beep 3 lần: ON 0.2s, OFF 0.2s
- Không bị méo tiếng hoặc rè

### Servo Test:
- Servo quay mượt mà từ 0° → 90° → 180°
- Không rung giật
- Giữ vị trí ổn định
- Không có tiếng kêu lạ

## 🎯 Quick Test Commands

```bash
# LED Đỏ
python3 -c "from gpiozero import LED; import time; led=LED(17); led.on(); time.sleep(2); led.off()"

# LED Xanh
python3 -c "from gpiozero import LED; import time; led=LED(27); led.on(); time.sleep(2); led.off()"

# LED Vàng
python3 -c "from gpiozero import LED; import time; led=LED(22); led.on(); time.sleep(2); led.off()"

# Buzzer
python3 -c "from gpiozero import Buzzer; import time; b=Buzzer(23); b.on(); time.sleep(1); b.off()"

# Servo
python3 -c "from gpiozero import Servo; import time; s=Servo(18); s.mid(); time.sleep(2); s.close()"
```

## 📝 Test Checklist

- [ ] LED Đỏ (GPIO17) blink OK
- [ ] LED Xanh (GPIO27) blink OK
- [ ] LED Vàng (GPIO22) blink OK
- [ ] Buzzer (GPIO23) beep OK
- [ ] Servo (GPIO18) quay OK
- [ ] Tất cả devices không có tiếng/mùi lạ
- [ ] Pi không restart khi test
- [ ] Không có component nóng bất thường

---

**Sau khi test OK hết, bạn có thể chạy IoT client chính!** 🎉

```bash
cd /home/pi/IoT-Nha-Thong-Minh/raspberry-pi
source venv/bin/activate
python src/iot_client.py
```
