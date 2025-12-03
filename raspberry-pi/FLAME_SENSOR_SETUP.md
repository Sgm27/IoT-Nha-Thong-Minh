# Hướng dẫn cài đặt Module Cảm biến Lửa

## Thông số Module

| Thông số | Giá trị |
|----------|---------|
| Điện áp hoạt động | 3.3V - 5V |
| Bước sóng phát hiện | 760nm - 1100nm |
| Góc phát hiện | ~60 độ |
| Khoảng cách phát hiện | ~80cm (bật lửa), xa hơn với ngọn lửa lớn |
| Đầu ra | DO (Digital) + AO (Analog) |
| IC so sánh | LM393 |
| Kích thước | 3.2cm x 1.4cm |

## Sơ đồ chân

```
Module Cảm biến Lửa
+------------------+
|  [Sensor]        |
|                  |
|  VCC  GND  DO  AO|
+---+---+---+---+--+
    |   |   |   |
    |   |   |   +-- Analog Output (không sử dụng)
    |   |   +------ Digital Output (kết nối với GPIO)
    |   +---------- Ground
    +-------------- 3.3V hoặc 5V
```

## Kết nối với Raspberry Pi

### Sơ đồ kết nối

```
Raspberry Pi 5                    Module Cảm biến Lửa
+-------------+                   +------------------+
|             |                   |                  |
| Pin 1 (3.3V)+------------------>+ VCC              |
|             |                   |                  |
| Pin 6 (GND) +------------------>+ GND              |
|             |                   |                  |
| Pin 18      +------------------>+ DO               |
| (GPIO24)    |                   |                  |
|             |                   | AO (không dùng)  |
+-------------+                   +------------------+
```

### Bảng kết nối chi tiết

| Module Pin | Raspberry Pi Pin | Mô tả |
|------------|------------------|-------|
| VCC | Pin 1 (3.3V) hoặc Pin 2 (5V) | Nguồn điện |
| GND | Pin 6 (Ground) | Đất |
| DO | Pin 18 (GPIO24) | Digital Output - phát hiện lửa |
| AO | Không kết nối | Analog Output (cần ADC) |

> **Lưu ý**: Bạn có thể sử dụng GPIO khác thay cho GPIO24. Chỉ cần cập nhật trong file `iot_client.py`.

## Nguyên lý hoạt động

1. **Khi không có lửa**:
   - Cảm biến không phát hiện bước sóng hồng ngoại từ lửa
   - Đầu ra DO = HIGH (1)
   - LED trên module TẮT

2. **Khi có lửa**:
   - Cảm biến phát hiện bước sóng hồng ngoại (760nm-1100nm)
   - Đầu ra DO = LOW (0)
   - LED trên module SÁNG

3. **Điều chỉnh độ nhạy**:
   - Xoay potentiometer (chiết áp) trên module
   - Xoay theo chiều kim đồng hồ: Giảm độ nhạy
   - Xoay ngược chiều kim đồng hồ: Tăng độ nhạy

## Cấu hình trong code

### 1. Trong `iot_client.py`

```python
# Thêm vào gpio_configs
"Cảm biến lửa": GPIODeviceConfig(
    gpio_pin=24,  # GPIO24 cho DO
    name="Cảm biến lửa",
    device_type=DeviceType.FLAME_SENSOR,
),
```

### 2. Cấu hình Flame Sensor Service

```python
flame_sensor_config = FlameSensorConfig(
    poll_interval=0.1,       # Đọc mỗi 100ms
    confirm_readings=3,       # 3 lần liên tiếp để xác nhận
    alert_cooldown=10.0,      # 10 giây giữa các alerts
    critical_threshold=10,    # 10 lần để mức critical
)
```

### 3. Các mức cảnh báo

| Mức | Điều kiện | Hành động |
|-----|-----------|-----------|
| WARNING | 1-2 lần phát hiện liên tiếp | Beep chậm (5 lần) |
| ALERT | 3+ lần liên tiếp | Beep nhanh (100 lần) |
| CRITICAL | 10+ lần liên tiếp | Beep liên tục (200 lần) |

## Test cảm biến

### 1. Test thủ công với Python

```python
from gpiozero import DigitalInputDevice

# Tạo input device
sensor = DigitalInputDevice(24, pull_up=True)

# Đọc giá trị
while True:
    value = sensor.value
    if value == 0:
        print("🔥 Phát hiện LỬA!")
    else:
        print("✓ Bình thường")
    time.sleep(0.5)
```

### 2. Chạy script test

```bash
cd /home/pi/IoT-Nha-Thong-Minh/raspberry-pi/scripts
python test-flame-sensor.py
```

### 3. Test với Mock Mode

```bash
# Không cần phần cứng thật
MOCK_MODE=true python src/iot_client.py
```

## Xử lý sự cố

### 1. Không phát hiện được lửa

- [ ] Kiểm tra kết nối dây
- [ ] Xác nhận GPIO đúng (GPIO24)
- [ ] Tăng độ nhạy bằng potentiometer
- [ ] Kiểm tra LED trên module có sáng không
- [ ] Thử đưa lửa gần hơn (trong góc 60 độ)

### 2. False positive (báo sai)

- [ ] Giảm độ nhạy bằng potentiometer
- [ ] Tăng `confirm_readings` trong config
- [ ] Kiểm tra có ánh sáng hồng ngoại mạnh không (đèn halogen, mặt trời)
- [ ] Đảm bảo cảm biến không hướng về phía cửa sổ

### 3. Buzzer không kêu

- [ ] Kiểm tra buzzer đã được cấu hình
- [ ] Xác nhận GPIO của buzzer (mặc định GPIO23)
- [ ] Kiểm tra kết nối dây buzzer

## Tích hợp với hệ thống

### Luồng xử lý

```
Cảm biến lửa → GPIO → Raspberry Pi → FlameSensorService
                                            ↓
                                    Phát hiện lửa?
                                            ↓ Có
                              +-------------+-------------+
                              ↓                           ↓
                         Kích hoạt Buzzer          Gửi WebSocket
                                                        ↓
                                                   Backend
                                                        ↓
                                            +----------+----------+
                                            ↓                     ↓
                                     Phát âm thanh         Gửi tới app
                                     cảnh báo              Android/Web
```

### WebSocket Message Format

```json
{
    "type": "hardware_fire_alert",
    "sensor_name": "Cảm biến lửa",
    "level": "alert",
    "message": "🔥 CẢNH BÁO CHÁY! Cảm biến 'Cảm biến lửa' xác nhận có lửa!",
    "consecutive_count": 5,
    "timestamp": 1699999999.123,
    "source": "flame_sensor_module"
}
```

## Mua sắm

Module cảm biến lửa có thể mua tại:
- Shopee/Lazada: Tìm "module cảm biến lửa" hoặc "flame sensor module"
- Điện tử Nshop, Cytron, Icdayroi...

Giá tham khảo: 15.000 - 30.000 VND
