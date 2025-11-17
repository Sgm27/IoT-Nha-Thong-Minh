# Breadboard Wiring Guide - Raspberry Pi 5

Hướng dẫn chi tiết kết nối LED, Buzzer, Servo trên breadboard.

## 🛠️ Linh kiện cần thiết

### Bắt buộc:
- [ ] Breadboard (830 holes hoặc lớn hơn)
- [ ] Dây jumper male-female (Pi → Breadboard): 10-15 sợi
- [ ] Dây jumper male-male (trên breadboard): 10-15 sợi
- [ ] LED: 3 bóng (đỏ, xanh, vàng)
- [ ] **Điện trở 330Ω** (orange-orange-brown): 3 cái cho LED
- [ ] Buzzer active 5V: 1 cái
- [ ] Servo SG90 hoặc MG90S: 1-2 cái
- [ ] (Tùy chọn) Nguồn ngoài 5V-2A cho servo

### Điện trở cho LED:

**Công thức tính:**
```
R = (Vsource - VLED) / ILED

Với Pi GPIO:
- Vsource = 3.3V (GPIO output)
- VLED = 2.0V (LED đỏ/vàng) hoặc 3.0V (LED xanh/trắng)
- ILED = 10mA (0.01A) - dòng an toàn cho LED

LED Đỏ/Vàng:  R = (3.3 - 2.0) / 0.01 = 130Ω → Dùng 220Ω hoặc 330Ω
LED Xanh/Trắng: R = (3.3 - 3.0) / 0.01 = 30Ω  → Dùng 220Ω hoặc 330Ω
```

**Khuyến nghị: Dùng 330Ω cho tất cả LED** (an toàn, sáng vừa đủ)

**Mã màu điện trở:**
- **220Ω**: Red-Red-Brown (đỏ-đỏ-nâu)
- **330Ω**: Orange-Orange-Brown (cam-cam-nâu) ⭐ **RECOMMENDED**
- **470Ω**: Yellow-Purple-Brown (vàng-tím-nâu) - LED mờ hơn nhưng an toàn hơn

## 📐 Breadboard Layout

### Cấu trúc Breadboard:

```
    a b c d e   f g h i j
    ─────────   ─────────
 1  ● ● ● ● ●   ● ● ● ● ●
 2  ● ● ● ● ●   ● ● ● ● ●
 3  ● ● ● ● ●   ● ● ● ● ●
... (tiếp tục đến row 30 hoặc 63)

[+] ●●●●●●●●●●●●●●●●●●  ← Power rail (+)
[-] ●●●●●●●●●●●●●●●●●●  ← Ground rail (-)
```

**Lưu ý:**
- Các holes trong cùng 1 hàng (a-e hoặc f-j) được nối với nhau
- Power rails (+/-) chạy dọc theo breadboard
- Khe giữa (e-f) để cắm IC chips

## 🔴 LED Circuit - Chi tiết

### LED 1 (Đỏ) - GPIO17

**Schematic:**
```
Raspberry Pi               Breadboard
Pin 11 (GPIO17) ────┐
                    │
                    ▼
              [Row 10, col a]
                    │
                    ├─── 330Ω Resistor ───┐
                    │                     │
                    │                [Row 10-12]
                    │                     │
                    │                     ▼
                    │              LED Anode (+)
                    │              [Row 15, col a]
                    │                     │
                    │                     │ LED body
                    │                     │
                    │              LED Cathode (-)
                    │              [Row 17, col a]
                    │                     │
                    └─────────────────────┼─── to GND rail
                                          │
Pin 6 (GND) ──────────────────────────── GND rail
```

**Trên Breadboard (Top View):**
```
Row   a   b   c   d   e     f   g   h   i   j
─────────────────────────────────────────────
 8
 9
10   🔌GPIO17                                ← Jumper từ Pi Pin 11
11   │
12   └─[330Ω]─┐                             ← Điện trở 330Ω
13            │
14            │
15            🔴 LED+                        ← LED Anode (chân dài)
16            │
17            🔴 LED-                        ← LED Cathode (chân ngắn)
18            │
19            └──────► GND rail             ← Jumper to ground
```

**Bước kết nối:**
1. Cắm jumper male-female từ **Pi Pin 11 (GPIO17)** vào **row 10, col a**
2. Cắm điện trở 330Ω: một đầu ở **row 10, col c**, đầu kia ở **row 15, col c**
3. Cắm **LED Anode (+, chân dài)** vào **row 15, col a**
4. Cắm **LED Cathode (-, chân ngắn)** vào **row 17, col a**
5. Cắm jumper từ **row 17, col c** vào **GND rail (-)** trên breadboard
6. Cắm jumper từ **Pi Pin 6 (GND)** vào **GND rail (-)**

### LED 2 (Xanh) - GPIO27

**Layout tương tự, khác row:**
```
Row   a   b   c   d   e
─────────────────────────
22   🔌GPIO27            ← Pi Pin 13
23   │
24   └─[330Ω]─┐
25            │
26            🟢 LED+ (xanh)
27            │
28            🟢 LED-
29            └──► GND rail
```

### LED 3 (Vàng) - GPIO22

```
Row   a   b   c   d   e
─────────────────────────
32   🔌GPIO22            ← Pi Pin 15
33   │
34   └─[330Ω]─┐
35            │
36            🟡 LED+ (vàng)
37            │
38            🟡 LED-
39            └──► GND rail
```

## 🔊 Buzzer Circuit

### Active Buzzer (có dao động sẵn)

**Schematic:**
```
Pi Pin 16 (GPIO23) ──► Buzzer (+)
                        Buzzer (-)  ──► GND
```

**Breadboard:**
```
Row   a   b   c   d   e
─────────────────────────
42   🔌GPIO23            ← Pi Pin 16
43   │
44   └──► 🔔 Buzzer+   ← Buzzer positive (có dấu + hoặc chân dài)
45        🔔 Buzzer-   ← Buzzer negative
46        └──► GND rail
```

**Lưu ý:**
- Active buzzer không cần điện trở
- Phân biệt +/- trên buzzer (thường có dấu + hoặc sticker)
- Nếu buzzer có 3 chân: dùng chân giữa (signal) và chân - (GND)

### Passive Buzzer (cần PWM)

Nếu dùng passive buzzer, kết nối vào GPIO18 (PWM pin):
```
GPIO18 ──► Buzzer Signal
GND    ──► Buzzer GND
```

## 🔄 Servo Motor

### Servo SG90/MG90S

**Schematic:**
```
Raspberry Pi              Servo
───────────              ─────
Pin 12 (GPIO18) ──────► Orange/Yellow (Signal)
Pin 2  (5V)     ──────► Red (VCC/Power)
Pin 6  (GND)    ──────► Brown/Black (GND)
```

**⚠️ CẢNH BÁO QUAN TRỌNG:**

1. **Dòng điện:**
   - 1 servo nhỏ (SG90): ~200mA khi idle, ~600mA khi hoạt động
   - Pi 5V pins có thể cung cấp ~1A total
   - ✅ **1 servo**: OK để cắm trực tiếp vào Pi
   - ⚠️ **2+ servos**: PHẢI dùng nguồn ngoài 5V-2A

2. **Kết nối với nguồn ngoài:**
   ```
   External 5V Power Supply    Servo           Raspberry Pi
   ─────────────────────      ─────           ────────────
   (+) 5V ──────────────────► Red (VCC)
   (-) GND ─────┬───────────► Brown (GND)
                │                              Pin 12 (GPIO18) ──► Orange (Signal)
                └───────────────────────────► Pin 6 (GND) ⚠️ CHUNG GND
   ```

**Breadboard Layout (1 Servo với Pi power):**
```
Row   a   b   c   d   e     f   g   h   i   j
─────────────────────────────────────────────────
50                      🔌5V from Pi Pin 2      ← Power rail (+)
51
52        🔄Servo                                ← Servo motor
53        ├─ Red ──────────► (+) power rail    ← VCC
54        ├─ Brown ─────────► (-) GND rail     ← GND
55        └─ Orange ◄──🔌GPIO18 (Pin 12)       ← Signal

GND rail (-) ◄─────────🔌GND from Pi Pin 6
```

**Nếu dùng nguồn ngoài (2+ servos):**
```
External Power Supply:
  (+) 5V ───────► (+) power rail on breadboard
  (-) GND ──┬───► (-) GND rail on breadboard
            │
            └───► Pi Pin 6 (GND) ⚠️ QUAN TRỌNG: Chung GND!

Servo 1:
  Signal ◄── GPIO18 (Pi Pin 12)
  VCC ────── (+) rail (external power)
  GND ────── (-) rail

Servo 2:
  Signal ◄── GPIO13 (Pi Pin 33)
  VCC ────── (+) rail (external power)
  GND ────── (-) rail
```

## 🎨 Complete Breadboard Layout

**Full circuit với 3 LED + 1 Buzzer + 1 Servo:**

```
    Power Rails                 Main Area
    [+] ●●●●●●●●               a b c d e   f g h i j
    [-] ●●●●●●●●               ─────────   ─────────
                             1
                             ...
                            10  🔌17 ─[330Ω]─┐
From Pi:                    15              🔴+     ← LED Đỏ
Pin 11 (GPIO17) ────────►   17              🔴-─► GND rail
Pin 13 (GPIO27) ────────►   22  🔌27 ─[330Ω]─┐
Pin 15 (GPIO22) ────────►   26              🟢+     ← LED Xanh
Pin 16 (GPIO23) ────────►   28              🟢-─► GND rail
Pin 12 (GPIO18) ────────►   32  🔌22 ─[330Ω]─┐
Pin 2  (5V)     ────────►   36              🟡+     ← LED Vàng
Pin 6  (GND)    ────────►   38              🟡-─► GND rail
                            42  🔌23 ───────┐
                            44              🔔+     ← Buzzer
                            46              🔔-─► GND rail
                            50                  (+) rail ◄──🔌5V (Pin 2)
                            52  🔄Servo
                            53  Red ──────────► (+) rail
                            54  Brown ────────► (-) rail
                            55  Orange ◄──🔌18

                            GND rail (-) ◄──────🔌GND (Pin 6)
```

## 📋 Shopping List với số lượng cụ thể

| Item | Số lượng | Ghi chú |
|------|----------|---------|
| Breadboard 830 holes | 1 | Full-size hoặc half-size |
| Jumper wires male-female 20cm | 10 sợi | Pi → Breadboard |
| Jumper wires male-male | 10 sợi | Trên breadboard |
| LED 5mm đỏ | 1 | Hoặc màu bất kỳ |
| LED 5mm xanh | 1 | |
| LED 5mm vàng | 1 | |
| **Điện trở 330Ω (orange-orange-brown)** | **3 cái** | ⭐ Cho 3 LED |
| Active Buzzer 5V | 1 | Có dấu + |
| Servo SG90 | 1-2 | Hoặc MG90S |
| (Optional) Nguồn ngoài 5V-2A | 1 | Nếu dùng 2+ servos |

**Tổng chi phí ước tính:** ~200k-300k VNĐ

## ⚡ Pin Assignment Summary

| Component | GPIO Pin | Physical Pin | Breadboard Row |
|-----------|----------|--------------|----------------|
| LED Đỏ | GPIO 17 | Pin 11 | Row 10-17 |
| LED Xanh | GPIO 27 | Pin 13 | Row 22-28 |
| LED Vàng | GPIO 22 | Pin 15 | Row 32-38 |
| Buzzer | GPIO 23 | Pin 16 | Row 42-46 |
| Servo Signal | GPIO 18 | Pin 12 | Row 55 |
| 5V (Servo) | 5V | Pin 2 | Power rail (+) |
| GND (All) | GND | Pin 6 | GND rail (-) |

## 🔍 How to Identify LED Polarity

**LED có 2 chân không đều:**
- ✅ **Anode (+)**: Chân DÀI - kết nối với điện trở → GPIO
- ❌ **Cathode (-)**: Chân NGẮN - kết nối với GND

**Hoặc nhìn vào bên trong LED:**
- Chân nhỏ hơn bên trong = Anode (+)
- Chân lớn hơn bên trong = Cathode (-)

**Nếu đã cắt chân ngắn:**
- Phần đế LED có mặt phẳng (flat edge) ở phía Cathode (-)

## ✅ Testing Checklist

### Before Powering On:

- [ ] Kiểm tra tất cả LED có điện trở 330Ω
- [ ] Kiểm tra LED polarity (chân dài vào +)
- [ ] Kiểm tra buzzer polarity (+/-)
- [ ] Kiểm tra servo wiring (Red=5V, Brown=GND, Orange=Signal)
- [ ] Kiểm tra tất cả GND được nối vào GND rail
- [ ] Kiểm tra không có short circuit (GPIO và GND không chạm nhau)
- [ ] Nếu dùng nguồn ngoài cho servo: kiểm tra đã chung GND với Pi

### After Powering On:

- [ ] Pi boot thành công (LED đỏ trên Pi sáng)
- [ ] Không có linh kiện nóng bất thường
- [ ] Test từng LED một với code
- [ ] Test buzzer
- [ ] Test servo (chậm rãi, quan sát dòng điện)

## 🐛 Common Mistakes & Solutions

### LED không sáng:

1. **Kiểm tra polarity** - Đổi chiều LED
2. **Kiểm tra điện trở** - Phải có 330Ω
3. **Kiểm tra wiring** - GPIO → Resistor → LED+ → LED- → GND
4. **Test LED trực tiếp** - Nối LED (với resistor) từ 3.3V pin → GND

### LED cháy (sáng rồi tắt, mùi khét):

- ❌ **Thiếu điện trở** - LUÔN dùng resistor cho LED!
- ❌ **Nối nhầm 5V** - GPIO chỉ 3.3V, đừng nối LED vào 5V pin

### Buzzer không kêu:

1. **Kiểm tra +/-** - Đổi chiều buzzer
2. **Active vs Passive** - Active buzzer chỉ cần HIGH/LOW, Passive cần PWM
3. **Test trực tiếp** - Nối Buzzer+ vào 3.3V, Buzzer- vào GND

### Servo không quay:

1. **Kiểm tra PWM pin** - PHẢI dùng GPIO 18, 13, 12, hoặc 19
2. **Kiểm tra nguồn** - Servo cần đủ dòng (600mA)
3. **Pi restart khi servo quay** - Servo hút quá nhiều dòng → Dùng nguồn ngoài
4. **Servo rung giật** - Nguồn yếu → Dùng nguồn ngoài 5V-2A

## 📸 Visual Reference

**Resistor Color Codes:**
```
330Ω Resistor:
   Band 1  Band 2  Band 3  Band 4
   Orange  Orange  Brown   Gold
   (3)     (3)     (×10)   (±5%)

   Value = 33 × 10 = 330Ω
```

**LED Pins:**
```
     ╭─────╮
     │ LED │
     ╰─┬─┬─╯
       │ │
       │ └── Cathode (-) [Short leg]
       │
       └──── Anode (+) [Long leg]
```

**Servo Wiring:**
```
Servo Connector (looking at wires):
   ┌────┬────┬────┐
   │Red │Brn │Org │
   │VCC │GND │Sig │
   └────┴────┴────┘
    ▲    ▲    ▲
    │    │    └─── GPIO18 (Signal)
    │    └──────── GND
    └───────────── 5V
```

## 🎓 Pro Tips

1. **Color coding jumpers:**
   - Đỏ = 5V / Power
   - Đen/Nâu = GND
   - Các màu khác = Signals

2. **Cable management:**
   - Giữ dây ngắn gọn
   - Tránh chéo dây
   - Dùng breadboard có nhiều power rails

3. **Safety first:**
   - Tắt nguồn Pi trước khi thay đổi wiring
   - Luôn kiểm tra polarity trước khi cắm điện
   - Bắt đầu với 1 LED đơn giản, test OK rồi mới thêm

4. **Breadboard tips:**
   - Test connectivity với multimeter
   - Cắm components chắc chắn vào breadboard
   - Giữ khoảng cách giữa các circuits

## ✨ You're Ready!

Với guide này, bạn có thể:
- ✅ Kết nối 3 LED với điện trở đúng giá trị
- ✅ Kết nối Buzzer
- ✅ Kết nối Servo an toàn
- ✅ Tránh được các lỗi thường gặp
- ✅ Debug khi có vấn đề

**Happy Building!** 🎉⚡🔌
