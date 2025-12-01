# Sơ đồ Breadboard trực quan - Raspberry Pi 5 IoT

Hình vẽ breadboard đầy đủ, dễ nhìn cho dự án IoT với 3 LED, 1 Buzzer, 1 Servo.

## 🎨 Sơ đồ Breadboard hoàn chỉnh

### Raspberry Pi 5 GPIO Pins cần dùng:

```
┌─────────────────────────────────────┐
│  Raspberry Pi 5 - GPIO Header       │
│                                     │
│  Pin 2  ──── 5V      (Đỏ)          │  → Cho Servo
│  Pin 6  ──── GND     (Đen)          │  → Ground chung
│  Pin 11 ──── GPIO17  (Tím)          │  → LED Đỏ
│  Pin 12 ──── GPIO18  (Cam)          │  → Servo Signal (PWM)
│  Pin 13 ──── GPIO27  (Xanh dương)   │  → LED Xanh
│  Pin 15 ──── GPIO22  (Vàng)         │  → LED Vàng
│  Pin 16 ──── GPIO23  (Xanh lá)      │  → Buzzer
│                                     │
└─────────────────────────────────────┘
```

### Breadboard Layout chi tiết:

```
                    BREADBOARD 830 HOLES
    ┌────────────────────────────────────────────────────────────┐
    │  (+) ████████████████████████████████████  Power Rail      │
    │  (-) ████████████████████████████████████  Ground Rail     │
    │                                                            │
    │       a    b    c    d    e       f    g    h    i    j   │
    │      ───  ───  ───  ───  ───     ───  ───  ───  ───  ─── │
    │                                                            │
    │   1   ●    ●    ●    ●    ●       ●    ●    ●    ●    ●   │
    │   2   ●    ●    ●    ●    ●       ●    ●    ●    ●    ●   │
    │   3   ●    ●    ●    ●    ●       ●    ●    ●    ●    ●   │
    │   4   ●    ●    ●    ●    ●       ●    ●    ●    ●    ●   │
    │   5   ●    ●    ●    ●    ●       ●    ●    ●    ●    ●   │
    │   6   ●    ●    ●    ●    ●       ●    ●    ●    ●    ●   │
    │   7   ●    ●    ●    ●    ●       ●    ●    ●    ●    ●   │
    │   8   ●    ●    ●    ●    ●       ●    ●    ●    ●    ●   │
    │   9   ●    ●    ●    ●    ●       ●    ●    ●    ●    ●   │
    │  10   🟣═══●════●════●════●       ●    ●    ●    ●    ●   │  ← GPIO17 (Pin 11)
    │  11   ●    ●    ●    ●    ●       ●    ●    ●    ●    ●   │
    │  12   ●   ┌┴┐   ●    ●    ●       ●    ●    ●    ●    ●   │  ← 330Ω Resistor
    │  13   ●   │R│   ●    ●    ●       ●    ●    ●    ●    ●   │     (Orange-Orange-Brown)
    │  14   ●   └┬┘   ●    ●    ●       ●    ●    ●    ●    ●   │
    │  15   ●    ╔════●════●════●       ●    ●    ●    ●    ●   │  ← LED Đỏ Anode (+)
    │  16   ●    ║🔴  ●    ●    ●       ●    ●    ●    ●    ●   │     (Chân dài)
    │  17   ●    ╚════●════●════●       ●    ●    ●    ●    ●   │  ← LED Đỏ Cathode (-)
    │  18   ●    │    ●    ●    ●       ●    ●    ●    ●    ●   │     (Chân ngắn)
    │  19   ●    └════════════════════════════════════► (-)     │  → To GND rail
    │  20   ●    ●    ●    ●    ●       ●    ●    ●    ●    ●   │
    │  21   ●    ●    ●    ●    ●       ●    ●    ●    ●    ●   │
    │  22   🔵═══●════●════●════●       ●    ●    ●    ●    ●   │  ← GPIO27 (Pin 13)
    │  23   ●    ●    ●    ●    ●       ●    ●    ●    ●    ●   │
    │  24   ●   ┌┴┐   ●    ●    ●       ●    ●    ●    ●    ●   │  ← 330Ω Resistor
    │  25   ●   │R│   ●    ●    ●       ●    ●    ●    ●    ●   │
    │  26   ●   └┬┘   ●    ●    ●       ●    ●    ●    ●    ●   │
    │  27   ●    ╔════●════●════●       ●    ●    ●    ●    ●   │  ← LED Xanh Anode (+)
    │  28   ●    ║🟢  ●    ●    ●       ●    ●    ●    ●    ●   │
    │  29   ●    ╚════●════●════●       ●    ●    ●    ●    ●   │  ← LED Xanh Cathode (-)
    │  30   ●    │    ●    ●    ●       ●    ●    ●    ●    ●   │
    │  31   ●    └════════════════════════════════════► (-)     │  → To GND rail
    │  32   🟡═══●════●════●════●       ●    ●    ●    ●    ●   │  ← GPIO22 (Pin 15)
    │  33   ●    ●    ●    ●    ●       ●    ●    ●    ●    ●   │
    │  34   ●   ┌┴┐   ●    ●    ●       ●    ●    ●    ●    ●   │  ← 330Ω Resistor
    │  35   ●   │R│   ●    ●    ●       ●    ●    ●    ●    ●   │
    │  36   ●   └┬┘   ●    ●    ●       ●    ●    ●    ●    ●   │
    │  37   ●    ╔════●════●════●       ●    ●    ●    ●    ●   │  ← LED Vàng Anode (+)
    │  38   ●    ║🟡  ●    ●    ●       ●    ●    ●    ●    ●   │
    │  39   ●    ╚════●════●════●       ●    ●    ●    ●    ●   │  ← LED Vàng Cathode (-)
    │  40   ●    │    ●    ●    ●       ●    ●    ●    ●    ●   │
    │  41   ●    └════════════════════════════════════► (-)     │  → To GND rail
    │  42   🟢═══●════●════●════●       ●    ●    ●    ●    ●   │  ← GPIO23 (Pin 16)
    │  43   ●    │    ●    ●    ●       ●    ●    ●    ●    ●   │
    │  44   ●   ┌┴────┴┐   ●    ●       ●    ●    ●    ●    ●   │  ← Buzzer (+)
    │  45   ●   │ 🔔  │   ●    ●       ●    ●    ●    ●    ●   │     (Active Buzzer)
    │  46   ●   └┬────┬┘   ●    ●       ●    ●    ●    ●    ●   │  ← Buzzer (-)
    │  47   ●    │    │    ●    ●       ●    ●    ●    ●    ●   │
    │  48   ●    └════════════════════════════════════► (-)     │  → To GND rail
    │  49   ●    ●    ●    ●    ●       ●    ●    ●    ●    ●   │
    │  50   ●    ●    ●    ●    ●       ●    ●    ●    ●    ●   │
    │  51   ●    ●    ●    ●    ●       ●    ●    ●    ●    ●   │
    │  52   ●    ●    ●    ●    ●      ┌──────────┐   ●    ●   │  ← Servo Motor
    │  53   ●    ●    ●    ●    ●      │  🔄 SG90 │   ●    ●   │     (Micro Servo)
    │  54   ●    ●    ●    ●    ●      └──┬──┬──┬─┘   ●    ●   │
    │  55   ●    ●    ●    ●    ●         │  │  │     ●    ●   │
    │  56   ●    ●    ●    ●    ●         │  │  │     ●    ●   │
    │  57   ●    ●    ●    ●    ●        🔴 🟤 🟠    ●    ●   │  ← Servo Wires
    │  58   ●    ●    ●    ●    ●         │  │  │     ●    ●   │     Red, Brown, Orange
    │  59   ●    ●    ●    ●    ●         │  │  └─────────────────► GPIO18 (Pin 12)
    │  60   ●    ●    ●    ●    ●         │  └──────────────────────► GND rail (-)
    │       ●    ●    ●    ●    ●         └─────────────────────────► 5V rail (+)
    │                                                            │
    │  (+) ◄════════════════════════════════════════════════════ 5V (Pin 2)
    │  (-) ◄════════════════════════════════════════════════════ GND (Pin 6)
    │                                                            │
    └────────────────────────────────────────────────────────────┘
```

## 📍 Vị trí chi tiết từng component

### 1. LED Đỏ (GPIO17)

```
Row 10: GPIO17 input
   ↓
Row 12-14: Điện trở 330Ω (┌─┐)
              │R│  = Orange-Orange-Brown
              └─┘
   ↓
Row 15-16: LED Anode (+) - Chân dài
              ║
              🔴
              ║
   ↓
Row 17: LED Cathode (-) - Chân ngắn
   ↓
Row 19: Jumper wire → GND rail
```

### 2. LED Xanh (GPIO27)

```
Row 22: GPIO27 input
Row 24-26: Điện trở 330Ω
Row 27-29: LED 🟢 (Anode row 27, Cathode row 29)
Row 31: → GND rail
```

### 3. LED Vàng (GPIO22)

```
Row 32: GPIO22 input
Row 34-36: Điện trở 330Ω
Row 37-39: LED 🟡 (Anode row 37, Cathode row 39)
Row 41: → GND rail
```

### 4. Buzzer (GPIO23)

```
Row 42: GPIO23 input
   ↓
Row 44-46: Buzzer 🔔
   ┌───┐
   │🔔 │  ← Active Buzzer
   └─┬─┘
     ↓
Row 48: → GND rail

Lưu ý: Buzzer có 2 chân, chân có dấu "+" vào row 44 (GPIO23)
       Chân "-" vào row 46 → GND
```

### 5. Servo Motor (GPIO18)

```
                ┌─────────┐
                │ 🔄 SG90 │
                └──┬─┬─┬──┘
                   │ │ │
                  🔴🟤🟠
                   │ │ │
                   │ │ └─► Orange wire → GPIO18 (Pin 12) - SIGNAL
                   │ └───► Brown wire  → GND rail (-)    - GND
                   └─────► Red wire    → 5V rail (+)     - POWER

⚠️ Quan trọng:
- Servo cần 5V, không phải 3.3V
- Dòng điện: ~200mA idle, ~600mA khi hoạt động
- Nếu dùng 2+ servos → Bắt buộc nguồn ngoài 5V-2A
```

## 🔌 Kết nối từ Raspberry Pi đến Breadboard

### Danh sách jumper wires cần dùng:

| # | Từ Pi | Màu đề xuất | Đến Breadboard | Ghi chú |
|---|-------|-------------|----------------|---------|
| 1 | Pin 2 (5V) | Đỏ | Power rail (+) | Nguồn 5V cho servo |
| 2 | Pin 6 (GND) | Đen | GND rail (-) | Ground chung |
| 3 | Pin 11 (GPIO17) | Tím | Row 10, col a | LED Đỏ signal |
| 4 | Pin 13 (GPIO27) | Xanh dương | Row 22, col a | LED Xanh signal |
| 5 | Pin 15 (GPIO22) | Vàng | Row 32, col a | LED Vàng signal |
| 6 | Pin 16 (GPIO23) | Xanh lá | Row 42, col a | Buzzer signal |
| 7 | Pin 12 (GPIO18) | Cam | Servo Orange wire | Servo PWM signal |

### Jumper wires trên breadboard (male-male):

| # | Từ | Đến | Mục đích |
|---|-------|-----|----------|
| 1 | Row 19, col c | GND rail | LED Đỏ → GND |
| 2 | Row 31, col c | GND rail | LED Xanh → GND |
| 3 | Row 41, col c | GND rail | LED Vàng → GND |
| 4 | Row 48, col c | GND rail | Buzzer → GND |

## 🎨 Hình vẽ từng bước lắp ráp

### Bước 1: Chuẩn bị breadboard và power rails

```
┌────────────────────────────────┐
│  (+) ████████████████  ← Chưa nối
│  (-) ████████████████  ← Chưa nối
│                                │
│  Breadboard trống              │
│                                │
└────────────────────────────────┘
```

### Bước 2: Nối power rails từ Pi

```
Raspberry Pi              Breadboard
   Pin 2 (5V) ═══🔴═════► (+) rail
   Pin 6 (GND) ══🔴═════► (-) rail
```

### Bước 3: Lắp LED Đỏ với resistor

```
     a    b    c    d    e
10  🟣───●────●────●  ← GPIO17
11   ●    ●    ●    ●
12   ●   ┌┴┐  ●    ●  ← 330Ω resistor
13   ●   │R│  ●    ●
14   ●   └┬┘  ●    ●
15   ●    ╔═══●════●  ← LED+ (chân dài)
16   ●    ║🔴 ●    ●
17   ●    ╚═══●════●  ← LED- (chân ngắn)
18   ●    │   ●    ●
19   ●    └───────────► GND rail
```

### Bước 4: Lặp lại cho LED Xanh (row 22) và LED Vàng (row 32)

### Bước 5: Lắp Buzzer

```
     a    b    c    d    e
42  🟢───●────●────●  ← GPIO23
43   ●    │   ●    ●
44   ●   ┌┴───┐ ●  ●  ← Buzzer (+)
45   ●   │🔔  │ ●  ●
46   ●   └┬───┘ ●  ●  ← Buzzer (-)
47   ●    │   ●    ●
48   ●    └───────────► GND rail
```

### Bước 6: Lắp Servo

```
Servo (nhìn từ phía dây):
   ┌───┬───┬───┐
   │Red│Brn│Org│
   └─┬─┴─┬─┴─┬─┘
     │   │   │
     ▼   ▼   ▼
    5V  GND GPIO18
```

## ⚡ Kiểm tra trước khi bật nguồn

### Checklist:

- [ ] **LED Đỏ (Row 10-19):**
  - [ ] GPIO17 vào row 10
  - [ ] Resistor 330Ω nối row 10 với row 15
  - [ ] LED chân dài (+) vào row 15
  - [ ] LED chân ngắn (-) vào row 17
  - [ ] Jumper từ row 19 vào GND rail

- [ ] **LED Xanh (Row 22-31):** (tương tự)
- [ ] **LED Vàng (Row 32-41):** (tương tự)

- [ ] **Buzzer (Row 42-48):**
  - [ ] GPIO23 vào row 42
  - [ ] Buzzer (+) vào row 44
  - [ ] Buzzer (-) vào row 46
  - [ ] Jumper từ row 48 vào GND rail

- [ ] **Servo:**
  - [ ] Red wire → 5V rail (+)
  - [ ] Brown wire → GND rail (-)
  - [ ] Orange wire → GPIO18 (Pi Pin 12)

- [ ] **Power Rails:**
  - [ ] Pi Pin 2 (5V) → Power rail (+)
  - [ ] Pi Pin 6 (GND) → GND rail (-)

- [ ] **Không có short circuit:**
  - [ ] Kiểm tra không có dây nào chạm nhau
  - [ ] Kiểm tra GPIO và GND không nối trực tiếp

## 🎯 Test từng component

### Test LED đơn lẻ (trên Pi):

```bash
# Test LED Đỏ (GPIO17)
gpio -g write 17 1  # Bật
sleep 1
gpio -g write 17 0  # Tắt

# Hoặc dùng Python
python3 << 'EOF'
from gpiozero import LED
import time

led = LED(17)
led.on()
time.sleep(1)
led.off()
EOF
```

### Test với IoT client (Mock mode):

```bash
cd /path/to/raspberry-pi
MOCK_MODE=true python3 src/iot_client.py
```

### Test với hardware thật:

```bash
cd /path/to/raspberry-pi
python3 src/iot_client.py
```

## 🔧 Troubleshooting Visual Guide

### LED không sáng - Kiểm tra polarity:

```
❌ SAI:
GPIO17 ──► [330Ω] ──► LED- ──► LED+ ──► GND
                       (ngắn)  (dài)

✅ ĐÚNG:
GPIO17 ──► [330Ω] ──► LED+ ──► LED- ──► GND
                       (dài)   (ngắn)
```

### Servo không quay - Kiểm tra PWM pin:

```
❌ SAI:
GPIO17 (không phải PWM pin) → Servo Orange

✅ ĐÚNG:
GPIO18 (PWM pin) → Servo Orange
```

## 📸 Hình ảnh reference

### Điện trở 330Ω:

```
  Band 1  Band 2  Band 3  Tolerance
   ┌─┐     ┌─┐     ┌─┐      ┌─┐
   │🟠│    │🟠│    │🟤│     │🟡│
   └─┘     └─┘     └─┘      └─┘
   (3)     (3)     (×10)    (±5%)

Value = 33 × 10 = 330Ω
```

### LED polarity:

```
     TOP VIEW          SIDE VIEW
      ╭───╮            ╭──╮
      │   │            │▓▓│ ← Rounded top
      ╰─┬─╯            │▓▓│
        │              ╰──╯
    ┌───┴───┐          │  │
    │       │          │  │
  Long    Short      Anode Cathode
   (+)     (-)        (+)   (-)
```

### Breadboard internal connections:

```
Power Rails (dọc):        Main area (ngang):

  (+) ●●●●●●●●●●●         a b c d e   f g h i j
       Connected          ─────────   ─────────
                       1  ●─●─●─●─●   ●─●─●─●─●
  (-) ●●●●●●●●●●●       2  ●─●─●─●─●   ●─●─●─●─●
       Connected             ↑         ↑
                          Connected  Connected
```

## ✅ Hoàn thành!

Với sơ đồ trên, bạn đã có đầy đủ thông tin để:
- ✅ Biết chính xác vị trí cắm từng component
- ✅ Hiểu cách kết nối điện trở với LED
- ✅ Phân biệt polarity của LED và Buzzer
- ✅ Kết nối Servo đúng cách và an toàn
- ✅ Kiểm tra và test từng bước

**Chúc bạn lắp ráp thành công!** 🎉

---

**Next steps:**
1. Lắp ráp theo sơ đồ trên
2. Kiểm tra lại tất cả kết nối
3. Bật Pi và test với code
4. Enjoy your smart home! 🏠✨
