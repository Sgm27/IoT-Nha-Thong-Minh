# Hướng dẫn lắp ráp Hardware - Raspberry Pi 5

## Danh sách linh kiện

### Bắt buộc

| Linh kiện | Mô tả | Ghi chú |
|-----------|-------|---------|
| Raspberry Pi 5 | 4GB RAM trở lên | Model mới nhất, hỗ trợ tốt USB 3.0 |
| Nguồn 5V-3A | Official Raspberry Pi PSU | Quan trọng cho ổn định |
| MicroSD 32GB+ | Class 10, A1 | Để cài OS và chạy code |
| USB Webcam | 720p trở lên | Logitech C920, C270 hoặc tương đương |
| USB Microphone | Bất kỳ | Hoặc webcam có mic tích hợp |
| Speaker | 3.5mm hoặc USB | Loa mini chủ động |
| Module Relay 4 kênh | 5V, active LOW | Với opto-isolator |
| Đèn LED 5V | 4-5 bóng | Để test, màu bất kỳ |
| Điện trở 220Ω | 4-5 cái | Hạn dòng cho LED |
| Dây jumper | Male-Female, 20cm | 10-15 sợi |
| Breadboard | Nhỏ | Để kết nối LED test |

### Tùy chọn

| Linh kiện | Mô tả | Công dụng |
|-----------|-------|-----------|
| Vỏ Pi + Quạt | Với tản nhiệt | Giảm nhiệt khi chạy liên tục |
| Nguồn ngoài 5V | Cho relay module | Giảm tải cho Pi |
| Thiết bị điện 220V | Đèn, quạt thật | CHỈ nếu có kinh nghiệm |
| Module cách ly | SSR 220V | An toàn hơn relay cơ |

## Sơ đồ kết nối

### 1. Relay Module → Raspberry Pi

```
Raspberry Pi 5 GPIO        Module Relay 4 Kênh
─────────────────          ───────────────────

5V (Pin 2 hoặc 4)  ────►   VCC
GND (Pin 6)        ────►   GND
GPIO17 (Pin 11)    ────►   IN1  [Phòng khách]
GPIO27 (Pin 13)    ────►   IN2  [Phòng ngủ]
GPIO22 (Pin 15)    ────►   IN3  [Nhà bếp]
GPIO23 (Pin 16)    ────►   IN4  [Ban công]
```

**Lưu ý quan trọng:**
- Module relay active LOW: GPIO HIGH = OFF, GPIO LOW = ON
- VCC của relay có thể dùng nguồn Pi hoặc nguồn ngoài 5V
- Nếu dùng nguồn ngoài: GND phải chung với Pi

### 2. LED Test → Relay Module

Mỗi relay điều khiển 1 đèn LED:

```
Relay Channel 1 (Phòng khách)
─────────────────────────────
5V ───► [COM]
        [NO] ───► LED+ ───► [220Ω] ───► GND
        [NC] (không dùng)


Tương tự cho Channel 2, 3, 4
```

**Giải thích:**
- COM: Common (nối với nguồn 5V)
- NO: Normally Open (nối với LED khi relay ON)
- NC: Normally Closed (không dùng)

### 3. USB Webcam

```
USB Webcam ───► USB Port trên Pi (USB 3.0 màu xanh)
```

**Kiểm tra:**
```bash
lsusb  # Xem webcam có được nhận diện
v4l2-ctl --list-devices  # List video devices
```

Webcam sẽ xuất hiện là `/dev/video0` hoặc `/dev/video1`

### 4. USB Microphone

```
USB Microphone ───► USB Port trên Pi
```

**Hoặc dùng webcam có mic tích hợp** (tiện hơn)

**Kiểm tra:**
```bash
arecord -l  # List recording devices
arecord -d 3 test.wav  # Test recording 3 giây
aplay test.wav  # Nghe lại
```

### 5. Speaker

**Option 1: 3.5mm Jack**
```
Speaker 3.5mm ───► Audio Jack trên Pi
```

**Option 2: USB Speaker**
```
USB Speaker ───► USB Port trên Pi
```

**Kiểm tra:**
```bash
aplay -l  # List playback devices
speaker-test -t wav -c 2  # Test speaker
```

## GPIO Pinout Raspberry Pi 5

```
   3.3V  (1) (2)  5V
  GPIO2  (3) (4)  5V
  GPIO3  (5) (6)  GND
  GPIO4  (7) (8)  GPIO14
    GND  (9) (10) GPIO15
 GPIO17 (11) (12) GPIO18   ◄── IN1 Relay (Phòng khách)
 GPIO27 (13) (14) GND      ◄── IN2 Relay (Phòng ngủ)
 GPIO22 (15) (16) GPIO23   ◄── IN3 Relay (Nhà bếp), IN4 Relay (Ban công)
   3.3V (17) (18) GPIO24
 GPIO10 (19) (20) GND
  GPIO9 (21) (22) GPIO25
 GPIO11 (23) (24) GPIO8
    GND (25) (26) GPIO7
...
```

**Chú ý:**
- Dùng BCM numbering (GPIO17, không phải Pin 11)
- 5V: Pin 2 hoặc Pin 4
- GND: Pin 6, 9, 14, 20, 25, 30, 34, 39

## Hướng dẫn lắp ráp từng bước

### Chuẩn bị

1. **Tắt nguồn Pi** - Rút điện trước khi làm việc
2. **Chuẩn bị workspace** - Bàn phẳng, có đủ ánh sáng
3. **Kiểm tra linh kiện** - Đảm bảo đủ và không hỏng
4. **Tĩnh điện** - Chạm tay vào vật kim loại để xả tĩnh điện

### Bước 1: Kết nối Relay Module

1. Đặt Pi và relay module lên bàn
2. Kết nối dây jumper:
   - **GND (Pi Pin 6) → GND (Relay)**
   - **5V (Pi Pin 2) → VCC (Relay)**
   - **GPIO17 (Pi Pin 11) → IN1 (Relay)**
   - **GPIO27 (Pi Pin 13) → IN2 (Relay)**
   - **GPIO22 (Pi Pin 15) → IN3 (Relay)**
   - **GPIO23 (Pi Pin 16) → IN4 (Relay)**

3. Kiểm tra lại kỹ:
   - Màu dây đúng chưa?
   - VCC/GND có bị ngược không?
   - Các chân GPIO đúng số chưa?

### Bước 2: Kết nối LED Test (trên breadboard)

Cho mỗi relay channel:

1. Cắm LED vào breadboard:
   - Chân dài (+) vào một hàng
   - Chân ngắn (-) vào hàng khác

2. Kết nối điện trở 220Ω:
   - Một đầu nối với LED- (chân ngắn)
   - Đầu kia nối GND

3. Kết nối relay:
   - Dây từ 5V → Relay COM
   - Dây từ Relay NO → LED+ (chân dài)

4. Lặp lại cho 4 LEDs (4 channels)

**Sơ đồ breadboard:**
```
     5V
      │
   ┌──┴──┐
   │ COM │
   │ NO──┼───► LED+ ───► [220Ω] ───► GND
   │ NC  │
   └─────┘
   Relay 1
```

### Bước 3: Kết nối USB Webcam

1. Cắm webcam vào USB port màu xanh (USB 3.0)
2. Đặt webcam ở vị trí hướng về khu vực cần giám sát
3. Có thể dùng giá đỡ hoặc kẹp gá

### Bước 4: Kết nối Microphone

- **Nếu dùng webcam có mic:** Không cần làm gì thêm
- **Nếu dùng USB mic riêng:** Cắm vào USB port còn lại

### Bước 5: Kết nối Speaker

- **Speaker 3.5mm:** Cắm vào jack audio trên Pi
- **USB speaker:** Cắm vào USB port

### Bước 6: Kiểm tra kết nối

**Checklist trước khi bật nguồn:**

- [ ] Tất cả dây jumper đã kết nối chắc chắn
- [ ] VCC và GND không bị ngược
- [ ] Không có chân GPIO nào chạm nhau
- [ ] LED đã có điện trở hạn dòng
- [ ] Webcam, mic, speaker đã cắm đúng port

### Bước 7: Bật nguồn và test

1. **Cắm nguồn vào Pi** - Đèn nguồn đỏ sáng
2. **Đợi Pi boot** - Đèn xanh nhấp nháy
3. **SSH vào Pi** hoặc kết nối màn hình
4. **Test từng component:**

```bash
# Test GPIO
python3 -c "from gpiozero import LED; led = LED(17); led.on(); input('Press Enter'); led.off()"

# Test camera
v4l2-ctl --list-devices
ffplay /dev/video0

# Test microphone
arecord -d 3 test.wav && aplay test.wav

# Test speaker
speaker-test -t wav -c 2
```

## Nâng cấp: Điều khiển thiết bị 220VAC thật

⚠️ **CẢNH BÁO NGHIÊM TRỌNG:**
- Điện 220VAC có thể gây chết người
- CHỈ làm nếu bạn có kiến thức điện
- Luôn tắt cầu dao trước khi làm việc
- Dùng thiết bị cách ly (Solid State Relay hoặc relay có opto-isolator)
- Tuân thủ quy định an toàn điện

**Không được:**
- Kết nối trực tiếp 220VAC vào relay module
- Làm việc với điện khi đang có nguồn
- Để dây điện trần, không cách điện

**Nên dùng:**
- Module SSR (Solid State Relay) cho 220VAC
- Hộp điện kín có cầu chì
- Ổ cắm thông minh có sẵn (dễ hơn và an toàn hơn)

## Sơ đồ tổng thể

```
                        ┌─────────────────┐
                        │ Raspberry Pi 5  │
                        │                 │
USB Webcam ────────────►│ USB 3.0        │
                        │                 │
USB Mic ───────────────►│ USB 2.0        │
                        │                 │
Speaker ────────────────│ 3.5mm Jack     │
                        │                 │
                        │ GPIO Pins:      │
                        │  17, 27, 22, 23 │
                        │  5V, GND        │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ Relay Module    │
                        │  4 Channel 5V   │
                        │                 │
                        │ IN1 IN2 IN3 IN4 │
                        │ [1] [2] [3] [4] │
                        └─┬───┬───┬───┬───┘
                          │   │   │   │
                          ▼   ▼   ▼   ▼
                        LED LED LED LED
                     (Test lights hoặc thiết bị thật)
```

## Troubleshooting

### Relay không hoạt động

1. **Kiểm tra LED trên relay module** - Có sáng không?
2. **Đo điện áp** - VCC có đủ 5V không?
3. **Test GPIO** - Chạy code test ở trên
4. **Kiểm tra active HIGH/LOW** - Thử đổi config `active_high`

### LED không sáng

1. **Kiểm tra LED** - Có bị cháy không? Test với pin 3V
2. **Kiểm tra cực tính** - Chân dài (+), chân ngắn (-)
3. **Kiểm tra điện trở** - Có đúng 220Ω không?
4. **Kiểm tra relay** - Có click không khi bật?

### Camera không nhận diện

1. **Thử USB port khác**
2. **Kiểm tra nguồn** - Webcam cần đủ điện
3. **Update firmware** - `sudo apt update && sudo apt upgrade`
4. **Kiểm tra driver** - `dmesg | grep video`

### Audio không hoạt động

1. **Chọn đúng device** - `sudo raspi-config` → Advanced → Audio
2. **Tăng volume** - `alsamixer`
3. **Kiểm tra ALSA** - `aplay -l`, `arecord -l`
4. **Reboot** - Đôi khi cần restart

## Bảo trì

### Hàng ngày
- Kiểm tra Pi có nóng quá không (thêm quạt nếu cần)
- Xem logs có lỗi không

### Hàng tuần
- Kiểm tra kết nối vật lý (dây jumper lỏng?)
- Vệ sinh bụi

### Hàng tháng
- Update OS: `sudo apt update && sudo apt upgrade`
- Backup SD card
- Kiểm tra relay module có bị oxy hóa không

## Tài liệu tham khảo

- [Raspberry Pi 5 GPIO Pinout](https://pinout.xyz/)
- [gpiozero Documentation](https://gpiozero.readthedocs.io/)
- [OpenCV Python Tutorials](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
- [PyAudio Documentation](https://people.csail.mit.edu/hubert/pyaudio/docs/)
