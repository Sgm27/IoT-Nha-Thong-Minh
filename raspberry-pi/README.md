# IoT Smart Home Client - Raspberry Pi 5

Client IoT chạy trên Raspberry Pi 5 để điều khiển thiết bị thông minh và streaming audio/video lên backend server.

## Tính năng

- ✅ **GPIO Control**: Điều khiển relay module 4 kênh để bật/tắt đèn
- ✅ **Camera Streaming**: Capture và gửi video từ USB webcam lên server
- ✅ **Audio I/O**: Thu âm từ microphone và phát audio từ speaker
- ✅ **WebSocket Client**: Kết nối realtime với backend server
- ✅ **Fire Detection**: Gửi camera frames cho backend để phát hiện cháy
- ✅ **Auto-reconnect**: Tự động kết nối lại khi mất kết nối
- ✅ **Systemd Service**: Tự động chạy khi khởi động Pi

## Yêu cầu Hardware

### Bắt buộc
- Raspberry Pi 5 (4GB RAM trở lên khuyến nghị)
- MicroSD card 32GB+
- Nguồn 5V-3A (official Raspberry Pi PSU)
- USB Webcam (hoặc Raspberry Pi Camera Module)
- USB Microphone
- Speaker (USB hoặc 3.5mm jack)
- Module relay 4 kênh 5V (active LOW)
- Dây jumper male-female
- Đèn LED 5V + điện trở (hoặc thiết bị thật)

### Tùy chọn
- Vỏ Pi kèm quạt/tản nhiệt
- Bộ nguồn cho relay module
- Thiết bị điện 220VAC (đèn, quạt) - CHỈ NẾU BẠN CÓ KINH NGHIỆM

## Kết nối GPIO

Module relay kết nối với Raspberry Pi GPIO (BCM numbering):

| Relay Channel | GPIO Pin | Mặc định điều khiển |
|---------------|----------|---------------------|
| IN1           | GPIO17   | Phòng khách         |
| IN2           | GPIO27   | Phòng ngủ           |
| IN3           | GPIO22   | Nhà bếp             |
| IN4           | GPIO23   | Ban công            |
| VCC           | 5V       | Nguồn relay         |
| GND           | GND      | Ground              |

**Lưu ý**: Module relay thường dùng logic **active LOW**:
- GPIO HIGH (3.3V) = Relay OFF
- GPIO LOW (0V) = Relay ON

## Cài đặt

### 1. Clone repository

```bash
cd /home/pi
git clone <repository-url> IoT-Nha-Thong-Minh
cd IoT-Nha-Thong-Minh/raspberry-pi
```

### 2. Chạy setup script

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

Script sẽ tự động:
- Cập nhật hệ thống
- Cài đặt dependencies (OpenCV, PyAudio, v4l-utils...)
- Tạo Python virtual environment
- Cài đặt Python packages
- Tạo file config
- Kiểm tra hardware
- Cấu hình permissions

### 3. Cấu hình

Chỉnh sửa file `config/.env`:

```bash
nano config/.env
```

**Quan trọng nhất**: Thay đổi `BACKEND_URL` thành địa chỉ backend server của bạn:

```bash
BACKEND_URL=ws://192.168.1.100:8000/ws/gemini
```

Các cấu hình khác (GPIO pins, camera settings, audio...) đã có giá trị mặc định hợp lý.

### 4. Kiểm tra hardware

#### Camera
```bash
# Liệt kê cameras
v4l2-ctl --list-devices

# Test camera (webcam USB thường là /dev/video0)
ffplay /dev/video0
```

#### Audio
```bash
# Liệt kê microphones
arecord -l

# Test recording
arecord -d 3 test.wav
aplay test.wav

# Liệt kê speakers
aplay -l
```

#### GPIO
```bash
# Kiểm tra GPIO pins (cài đặt gpioinfo nếu chưa có)
sudo apt-get install gpiod
gpioinfo
```

### 5. Kết nối relay module

**⚠️ CẢNH BÁO AN TOÀN:**
- Tắt nguồn Pi trước khi kết nối
- Kiểm tra kỹ VCC/GND trước khi bật nguồn
- KHÔNG làm việc với điện 220VAC nếu chưa có kinh nghiệm

Kết nối relay module:

1. **GND của relay → GND của Pi**
2. **VCC của relay → 5V của Pi** (hoặc nguồn ngoài 5V)
3. **IN1 → GPIO17** (Phòng khách)
4. **IN2 → GPIO27** (Phòng ngủ)
5. **IN3 → GPIO22** (Nhà bếp)
6. **IN4 → GPIO23** (Ban công)

Kết nối đèn LED test:
- LED Anode (+) → Relay NO (Normally Open)
- LED Cathode (-) → GND (qua điện trở 220Ω)
- Relay COM → 5V

## Chạy thử

### Chế độ thường

```bash
cd /home/pi/IoT-Nha-Thong-Minh/raspberry-pi
source .venv/bin/activate
python3 src/iot_client.py
```

### Chế độ MOCK (test không cần hardware)

```bash
MOCK_MODE=true python3 src/iot_client.py
```

## Cài đặt systemd service (auto-start)

Để IoT client tự động chạy khi Pi khởi động:

```bash
# Cài đặt service
sudo ./scripts/install-service.sh

# Khởi động service
sudo systemctl start iot-client

# Kiểm tra trạng thái
sudo systemctl status iot-client

# Xem logs realtime
sudo journalctl -u iot-client -f
```

Các lệnh hữu ích:
```bash
sudo systemctl stop iot-client      # Dừng service
sudo systemctl restart iot-client   # Restart service
sudo systemctl disable iot-client   # Tắt auto-start
```

Gỡ cài đặt service:
```bash
sudo ./scripts/uninstall-service.sh
```

## Troubleshooting

### Camera không hoạt động

```bash
# Kiểm tra camera được nhận diện
lsusb
v4l2-ctl --list-devices

# Test camera với OpenCV
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAIL')"
```

### Audio không hoạt động

```bash
# Kiểm tra ALSA
arecord -l  # Microphones
aplay -l    # Speakers

# Test microphone
arecord -d 3 -f cd test.wav
aplay test.wav

# Điều chỉnh volume
alsamixer
```

### GPIO không hoạt động

```bash
# Kiểm tra user trong gpio group
groups

# Nếu không có, thêm vào:
sudo usermod -a -G gpio $USER
# Sau đó logout/login lại

# Test GPIO bằng Python
python3 -c "from gpiozero import LED; led = LED(17); led.on(); led.off(); print('OK')"
```

### WebSocket không kết nối

```bash
# Kiểm tra network
ping <backend-ip>

# Kiểm tra backend có chạy không
curl http://<backend-ip>:8000

# Kiểm tra WebSocket endpoint
wscat -c ws://<backend-ip>:8000/ws/gemini
```

### Permission denied errors

```bash
# Thêm user vào các groups cần thiết
sudo usermod -a -G gpio,audio,video $USER

# Logout/login lại để áp dụng
```

## Cấu trúc thư mục

```
raspberry-pi/
├── src/
│   ├── __init__.py
│   ├── iot_client.py           # Main entry point
│   ├── gpio_controller.py      # GPIO/Relay control
│   ├── camera_service.py       # USB webcam capture
│   ├── audio_handler.py        # Microphone/Speaker I/O
│   └── websocket_client.py     # WebSocket communication
├── config/
│   ├── .env.example            # Config template
│   ├── .env                    # Your config (gitignored)
│   └── config.py               # Config loader
├── scripts/
│   ├── setup.sh                # Setup script
│   ├── iot-client.service      # Systemd service file
│   ├── install-service.sh      # Install service
│   └── uninstall-service.sh    # Uninstall service
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│              IoT Client (Pi)                    │
│                                                 │
│  ┌─────────────┐  ┌──────────────┐            │
│  │   Camera    │  │ Microphone   │            │
│  │  Service    │  │   Handler    │            │
│  └──────┬──────┘  └──────┬───────┘            │
│         │                 │                     │
│         ▼                 ▼                     │
│  ┌────────────────────────────────┐            │
│  │    WebSocket Client            │◄──────┐    │
│  │  (Gemini Realtime Protocol)    │       │    │
│  └────────────┬───────────────────┘       │    │
│               │                            │    │
│               ▼                            │    │
│  ┌────────────────────────┐               │    │
│  │   GPIO Controller      │               │    │
│  │   (Relay Module)       │               │    │
│  └────────┬───────────────┘               │    │
│           │                                │    │
│           ▼                                │    │
│     ┌────────┐                             │    │
│     │  LEDs  │                     Audio   │    │
│     └────────┘                     Output  │    │
│                                        ▼   │    │
│                                   ┌──────────┐  │
│                                   │ Speaker  │  │
│                                   └──────────┘  │
└─────────────────────────────────────────────────┘
                     │
                     │ WebSocket
                     ▼
           ┌──────────────────┐
           │  Backend Server  │
           │   (FastAPI)      │
           └──────────────────┘
```

## Testing

### Mock Mode

Chạy ở chế độ mock để test logic mà không cần hardware:

```bash
MOCK_MODE=true python3 src/iot_client.py
```

Ở chế độ này:
- GPIO sẽ log actions thay vì điều khiển pins thật
- Camera tạo frames đen có timestamp
- Audio không capture/playback thật

### Test từng component

```python
# Test GPIO
from src.gpio_controller import GPIOController, RelayConfig

gpio = GPIOController({
    "test": RelayConfig(gpio_pin=17, location="Test Light")
}, mock_mode=True)
gpio.turn_on("test")
gpio.turn_off("test")

# Test Camera
from src.camera_service import CameraService, CameraConfig

camera = CameraService(CameraConfig(device_index=0))
camera.initialize()
camera.set_frame_callback(lambda frame: print(f"Frame: {len(frame)} bytes"))
camera.start_capture()

# Test Audio
from src.audio_handler import AudioHandler, AudioConfig

audio = AudioHandler(AudioConfig())
audio.initialize()
audio.start_recording()
audio.start_playback()
```

## Contributing

Khi thêm tính năng mới:
1. Tạo module riêng trong `src/`
2. Implement với mock mode support
3. Thêm config vào `config.py` và `.env.example`
4. Update documentation

## License

MIT License

## Support

Nếu gặp vấn đề, kiểm tra:
1. Logs: `sudo journalctl -u iot-client -f`
2. Hardware connections
3. Config file (`config/.env`)
4. Permissions (gpio, audio, video groups)

Để báo lỗi, tạo issue với:
- Raspberry Pi model và OS version
- Logs (`journalctl -u iot-client --no-pager -n 100`)
- Hardware setup
- Config file (KHÔNG bao gồm sensitive info)
