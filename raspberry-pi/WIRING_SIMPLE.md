# Hướng dẫn kết nối đơn giản - Raspberry Pi 5 IoT

Hướng dẫn kết nối từng component một, dễ hiểu, không cần biết nhiều về breadboard.

## 🎯 Tổng quan nhanh

Bạn cần kết nối **7 dây từ Raspberry Pi** và **3 điện trở trên breadboard**.

### Raspberry Pi → Breadboard (7 dây jumper):

```
Raspberry Pi                                    Breadboard
┌──────────────────┐
│ Pin 2  (5V)   ●  │ ─────[Đỏ]─────────► Power rail (+)
│ Pin 6  (GND)  ●  │ ─────[Đen]─────────► Ground rail (-)
│ Pin 11 (GPIO17)● │ ─────[Màu 1]───────► LED Đỏ
│ Pin 12 (GPIO18)● │ ─────[Cam]─────────► Servo (dây cam)
│ Pin 13 (GPIO27)● │ ─────[Màu 2]───────► LED Xanh
│ Pin 15 (GPIO22)● │ ─────[Màu 3]───────► LED Vàng
│ Pin 16 (GPIO23)● │ ─────[Màu 4]───────► Buzzer
└──────────────────┘
```

## 📦 Chuẩn bị

### Bạn cần:
- [ ] Raspberry Pi 5
- [ ] Breadboard (bất kỳ size nào)
- [ ] 3 LED (đỏ, xanh, vàng)
- [ ] 3 điện trở 330Ω (cam-cam-nâu)
- [ ] 1 Buzzer active 5V
- [ ] 1 Servo SG90
- [ ] 7 dây jumper male-female (Pi → breadboard)
- [ ] 4-5 dây jumper male-male (trên breadboard)

## 🔴 LED - Kết nối đơn giản

### Cách LED hoạt động:

```
GPIO pin ──► [Điện trở 330Ω] ──► LED+ ──► LED- ──► GND
              (bảo vệ LED)       (dài)    (ngắn)
```

### Mỗi LED cần 3 bước:

#### LED Đỏ (GPIO17):

```
BƯỚC 1: Pi Pin 11 ──► Cắm vào breadboard (gọi là điểm A)

BƯỚC 2: Cắm điện trở 330Ω
        - Chân 1 của điện trở → cùng hàng với điểm A (nối với GPIO17)
        - Chân 2 của điện trở → hàng khác (gọi là điểm B)

BƯỚC 3: Cắm LED
        - Chân DÀI (+) của LED → cùng hàng với điểm B (nối với điện trở)
        - Chân NGẮN (-) của LED → hàng khác (gọi là điểm C)

BƯỚC 4: Nối điểm C → GND rail (dây đen)
```

**Hình vẽ:**
```
Raspberry Pi Pin 11 (GPIO17)
        │
        ▼
    [điểm A] ──── Cắm vào breadboard
        │
        ├──── Chân 1 điện trở 330Ω
        │
        └──── Chân 2 điện trở 330Ω
                    │
                [điểm B]
                    │
                    ├──── LED chân dài (+)
                    │
                    └──── LED chân ngắn (-)
                              │
                          [điểm C]
                              │
                              ▼
                         GND rail (-)
```

#### LED Xanh (GPIO27) và LED Vàng (GPIO22):
**Làm y hệt như LED Đỏ**, chỉ khác:
- LED Xanh: Dùng Pi Pin 13 (GPIO27)
- LED Vàng: Dùng Pi Pin 15 (GPIO22)

## 🔊 Buzzer - Cực kỳ đơn giản!

Buzzer chỉ cần 2 dây, KHÔNG cần điện trở:

```
BƯỚC 1: Pi Pin 16 (GPIO23) ──► Buzzer chân (+)
BƯỚC 2: Buzzer chân (-) ──────► GND rail
```

**Phân biệt +/- trên buzzer:**
- Thường có dấu **+** in trên buzzer
- Hoặc chân dài = (+), chân ngắn = (-)
- Hoặc có sticker đỏ = (+), đen = (-)

- **Hình vẽ:**
```
Pi Pin 16 (GPIO23)
        │
        ▼
    Buzzer (+) ────┐
                   │
                   │  Buzzer
                   │
    Buzzer (-) ────┘
        │
        ▼
    GND rail (-)
```

## 🔄 Servo - Chỉ cắm 3 dây!

Servo có sẵn 3 dây màu, chỉ việc cắm:

```
BƯỚC 1: Servo dây ĐỎ    ──► Pi Pin 2 (5V)
BƯỚC 2: Servo dây NÂU   ──► Pi Pin 6 (GND) hoặc GND rail
BƯỚC 3: Servo dây CAM   ──► Pi Pin 12 (GPIO18)
```

**Hình vẽ:**
```
        Servo Motor SG90
        ┌──────────┐
        │    🔄    │
        └─┬──┬──┬──┘
          │  │  │
         🔴 🟤 🟠
          │  │  │
          │  │  └────► Pi Pin 12 (GPIO18) - Signal
          │  └───────► Pi Pin 6 (GND) - Ground
          └──────────► Pi Pin 2 (5V) - Power
```

**⚠️ Lưu ý:**
- 1 servo OK
- 2+ servo → Dùng nguồn ngoài 5V (không cắm dây đỏ vào Pi, cắm vào nguồn ngoài)

## 🔌 Power Rails - Quan trọng!

Breadboard có 2 rail dọc theo cạnh:
- **(+) rail** - Đường dương (thường màu đỏ)
- **(-) rail** - Đường âm/GND (thường màu xanh/đen)

**Kết nối:**
```
Pi Pin 2 (5V)  ──► (+) rail
Pi Pin 6 (GND) ──► (-) rail
```

**Tất cả GND đều nối vào (-) rail:**
- LED Đỏ chân ngắn → (-) rail
- LED Xanh chân ngắn → (-) rail
- LED Vàng chân ngắn → (-) rail
- Buzzer chân (-) → (-) rail
- Servo dây nâu → (-) rail (hoặc trực tiếp vào Pi Pin 6)

## 📝 Tóm tắt tất cả kết nối

### Từ Raspberry Pi ra ngoài (7 dây):

| Dây # | Từ Pi Pin | Đi đến | Ghi chú |
|-------|-----------|--------|---------|
| 1 | Pin 2 (5V) | (+) rail | Dây màu đỏ |
| 2 | Pin 6 (GND) | (-) rail | Dây màu đen |
| 3 | Pin 11 (GPIO17) | LED Đỏ circuit | Qua điện trở 330Ω |
| 4 | Pin 12 (GPIO18) | Servo dây cam | Trực tiếp |
| 5 | Pin 13 (GPIO27) | LED Xanh circuit | Qua điện trở 330Ω |
| 6 | Pin 15 (GPIO22) | LED Vàng circuit | Qua điện trở 330Ω |
| 7 | Pin 16 (GPIO23) | Buzzer (+) | Trực tiếp |

### Trên breadboard (4-5 dây jumper male-male):

| Dây # | Từ | Đến | Mục đích |
|-------|-----|-----|----------|
| 1 | LED Đỏ chân (-) | (-) rail | GND |
| 2 | LED Xanh chân (-) | (-) rail | GND |
| 3 | LED Vàng chân (-) | (-) rail | GND |
| 4 | Buzzer (-) | (-) rail | GND |
| 5 | (Tùy chọn) Servo nâu | (-) rail | Nếu không cắm trực tiếp vào Pi |

## 🎨 Sơ đồ tổng thể đơn giản

```
                    RASPBERRY PI 5
                    ┌────────────┐
        ┌───────────┤ Pin 2 (5V) │
        │           └────────────┘
        │           ┌────────────┐
        ├───────────┤ Pin 6 (GND)│
        │           └────────────┘
        │           ┌────────────┐
        │      ┌────┤ Pin 11     │ GPIO17 → LED Đỏ
        │      │    └────────────┘
        │      │    ┌────────────┐
        │      │ ┌──┤ Pin 12     │ GPIO18 → Servo (cam)
        │      │ │  └────────────┘
        │      │ │  ┌────────────┐
        │      │ │┌─┤ Pin 13     │ GPIO27 → LED Xanh
        │      │ ││ └────────────┘
        │      │ ││ ┌────────────┐
        │      │ ││┌┤ Pin 15     │ GPIO22 → LED Vàng
        │      │ │││└────────────┘
        │      │ │││┌────────────┐
        │      │ ││││ Pin 16     │ GPIO23 → Buzzer
        │      │ ││││└────────────┘
        │      │ ││││
        ▼      ▼ ▼▼▼▼
    ┌────────────────────────────────┐
    │        BREADBOARD              │
    │                                │
    │  (+) ████████ ◄── 5V (dây đỏ) │
    │  (-) ████████ ◄── GND (dây đen)│
    │                                │
    │  [330Ω] ─► LED Đỏ ──┐         │
    │  [330Ω] ─► LED Xanh ┤         │
    │  [330Ω] ─► LED Vàng ┤         │
    │  Buzzer ─────────────┤         │
    │  (tất cả nối GND)────┴─► (-)  │
    │                                │
    └────────────────────────────────┘
              │
        Servo motor ┌────┐
        ├─ Đỏ ──────┤ 5V │
        ├─ Nâu ─────┤GND │
        └─ Cam ─────┤Sig │
                    └────┘
```

## 🛠️ Hướng dẫn lắp ráp từng bước

### Bước 1: Chuẩn bị breadboard
- Đặt breadboard trước mặt
- Xác định (+) rail và (-) rail (thường ở 2 bên)

### Bước 2: Nối power từ Pi
```
Dây 1: Pi Pin 2 → (+) rail (dây đỏ)
Dây 2: Pi Pin 6 → (-) rail (dây đen)
```

### Bước 3: Lắp LED Đỏ
```
a) Chọn một vị trí trên breadboard (ví dụ row 10)
b) Cắm dây từ Pi Pin 11 vào row 10
c) Cắm điện trở 330Ω:
   - Chân 1 vào row 10 (cùng hàng với dây GPIO17)
   - Chân 2 vào row 15
d) Cắm LED:
   - Chân DÀI (+) vào row 15 (cùng với điện trở)
   - Chân NGẮN (-) vào row 17
e) Dây jumper: row 17 → (-) rail
```

### Bước 4: Lắp LED Xanh
```
Làm y hệt Bước 3, nhưng:
- Dùng row khác (ví dụ row 20)
- Dây từ Pi Pin 13 thay vì Pin 11
```

### Bước 5: Lắp LED Vàng
```
Làm y hệt Bước 3, nhưng:
- Dùng row khác (ví dụ row 30)
- Dây từ Pi Pin 15 thay vì Pin 11
```

### Bước 6: Lắp Buzzer
```
a) Chọn vị trí (ví dụ row 40)
b) Dây từ Pi Pin 16 → Buzzer chân (+)
c) Buzzer chân (-) → (-) rail
```

### Bước 7: Lắp Servo
```
a) Servo dây ĐỎ → Pi Pin 2 (5V)
b) Servo dây NÂU → Pi Pin 6 (GND) hoặc (-) rail
c) Servo dây CAM → Pi Pin 12 (GPIO18)
```

### Bước 8: Kiểm tra lại
- [ ] Tất cả LED đều có điện trở 330Ω
- [ ] LED chân dài (+) nối với điện trở
- [ ] LED chân ngắn (-) nối với GND
- [ ] Buzzer có phân biệt +/-
- [ ] Servo 3 dây đúng màu: Đỏ=5V, Nâu=GND, Cam=GPIO18
- [ ] Không có dây nào chạm nhau (short circuit)

## 🧪 Test nhanh

### Test LED bằng tay (không cần code):

```
Tắt Pi → Rút dây LED ra khỏi GPIO
→ Cắm trực tiếp dây đó vào Pin 1 (3.3V)
→ LED sáng = OK! ✅
→ LED không sáng = Kiểm tra lại polarity hoặc điện trở
```

### Test với Python:

```bash
# Trên Raspberry Pi
python3 << 'EOF'
from gpiozero import LED
import time

# Test LED Đỏ
led = LED(17)
led.on()
print("LED Đỏ sáng - check xem!")
time.sleep(2)
led.off()
print("LED Đỏ tắt")
EOF
```

## 💡 Tips quan trọng

### 1. Nhận biết chân LED:
```
     LED
    ╭───╮
    │ ● │
    ╰─┬─╯
      │ │
      │ └─── Chân NGẮN = (-) Cathode
      │
      └───── Chân DÀI = (+) Anode
```

Nếu cắt 2 chân bằng nhau rồi:
- Nhìn đế LED → Có 1 cạnh PHẲNG → Đó là phía (-)

### 2. Điện trở 330Ω:
```
Màu của 3 vòng đầu:
┌────┬────┬────┐
│ 🟠 │ 🟠 │ 🟤 │  = 330Ω ✅
└────┴────┴────┘
 Cam  Cam  Nâu
```

### 3. Servo dây:
- Thường có 3 màu: **Đỏ, Nâu (hoặc Đen), Cam (hoặc Vàng/Trắng)**
- **ĐỎ luôn là nguồn (+)**
- **NÂU/ĐEN luôn là GND (-)**
- **CAM/VÀNG/TRẮNG luôn là Signal**

### 4. Breadboard:
- Các lỗ trong **cùng 1 hàng ngang** (5 lỗ) **nối với nhau**
- Power rails **(+) và (-)** chạy **dọc** theo breadboard

```
Row 10:  a──b──c──d──e     f──g──h──i──j
         └──connected──┘    └──connected──┘
         (5 holes)          (5 holes)
```

## ❌ Lỗi thường gặp

### LED không sáng:
1. ❌ Cắm ngược LED → ✅ Đổi chiều (chân dài vào +)
2. ❌ Thiếu điện trở → ✅ Thêm 330Ω
3. ❌ Điện trở sai vị trí → ✅ Phải ở giữa GPIO và LED+
4. ❌ Không nối GND → ✅ LED- phải nối GND rail

### Buzzer không kêu:
1. ❌ Cắm ngược +/- → ✅ Đổi chiều
2. ❌ Passive buzzer (cần PWM) → ✅ Dùng active buzzer hoặc kết nối vào GPIO18

### Servo không quay:
1. ❌ Dùng GPIO thường → ✅ Phải dùng GPIO18 (PWM pin)
2. ❌ Thiếu nguồn → ✅ Kiểm tra dây đỏ nối 5V
3. ❌ Pi restart → ✅ Servo hút nhiều điện → Dùng nguồn ngoài

## ✅ Hoàn thành!

Sau khi lắp xong, bạn có:
- ✅ 3 LED (đỏ, xanh, vàng) điều khiển được
- ✅ 1 Buzzer để phát âm thanh
- ✅ 1 Servo để điều khiển góc quay

**Chạy IoT client:**
```bash
cd raspberry-pi
python3 src/iot_client.py
```

**Gemini sẽ có thể điều khiển:**
- "Bật đèn đỏ" → LED đỏ sáng
- "Tắt đèn xanh" → LED xanh tắt
- "Mở cửa" → Servo quay
- Cảnh báo cháy → Buzzer kêu

**Chúc mừng! Bạn đã hoàn thành IoT Smart Home!** 🎉🏠✨
