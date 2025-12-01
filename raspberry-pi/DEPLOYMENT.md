# Hướng dẫn Deploy lên Raspberry Pi

Hướng dẫn push code và setup IoT client trên Raspberry Pi 5.

## 📋 Thông tin kết nối

- **Hostname:** `raspberry.local`
- **IP Address:** `169.254.165.225`
- **Username:** `pi`
- **Password:** `1012004`

## 🚀 Cách 1: Deploy tự động (Khuyến nghị)

### Bước 1: Cài đặt sshpass (chỉ cần 1 lần)

```bash
# macOS
brew install hudochenkov/sshpass/sshpass

# Linux
sudo apt-get install sshpass
```

### Bước 2: Chạy deploy script

```bash
cd raspberry-pi
./scripts/deploy-to-pi.sh
```

Script sẽ tự động:
- ✅ Test SSH connection
- ✅ Sync tất cả files lên Pi
- ✅ Cài đặt dependencies
- ✅ Setup Python virtual environment
- ✅ Tạo config file

## 🔧 Cách 2: Deploy thủ công

### Bước 1: Test SSH connection

```bash
# Thử kết nối bằng hostname
ssh pi@raspberry.local
# Password: 1012004

# Nếu không được, thử IP
ssh pi@169.254.165.225
```

**Nếu không kết nối được:**
1. Kiểm tra Pi đã bật
2. Kiểm tra Pi và máy tính cùng mạng
3. Enable SSH trên Pi: `sudo raspi-config` → Interface Options → SSH → Enable

### Bước 2: Sync files lên Pi

```bash
# Từ thư mục raspberry-pi/
cd /Users/h3nr1.d14z/Projects/HieuLD/IoT-Nha-Thong-Minh/raspberry-pi

# Tạo thư mục trên Pi
ssh pi@raspberry.local "mkdir -p /home/pi/IoT-Nha-Thong-Minh/raspberry-pi"

# Copy files (sẽ hỏi password nhiều lần)
rsync -avz --progress \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude 'venv' \
    --exclude '.DS_Store' \
    ./ \
    pi@raspberry.local:/home/pi/IoT-Nha-Thong-Minh/raspberry-pi/
```

### Bước 3: SSH vào Pi và setup

```bash
ssh pi@raspberry.local
# Password: 1012004

cd /home/pi/IoT-Nha-Thong-Minh/raspberry-pi
```

### Bước 4: Cài đặt dependencies

```bash
# Update system
sudo apt-get update

# Cài đặt system packages
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    libgpiod2 \
    python3-opencv \
    portaudio19-dev \
    libasound2-dev \
    v4l-utils

# Tạo Python virtual environment
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Cài đặt Python packages
pip install -r requirements.txt
```

### Bước 5: Cấu hình

```bash
# Copy example config
cp config/.env.example config/.env

# Chỉnh sửa config
nano config/.env
```

**Cần sửa trong `.env`:**
```bash
# WebSocket server URL - Thay bằng IP backend của bạn
WEBSOCKET_SERVER_URL=ws://192.168.1.100:8000/ws/gemini

# Camera
CAMERA_DEVICE_INDEX=0
CAMERA_WIDTH=1280
CAMERA_HEIGHT=720
CAMERA_FPS=30

# Mock mode (false khi chạy thật)
MOCK_MODE=false
```

### Bước 6: Chạy thử

```bash
# Activate venv (nếu chưa)
source venv/bin/activate

# Chạy IoT client
python src/iot_client.py
```

**Nếu thành công, bạn sẽ thấy:**
```
========================================
IoT Smart Home Client - Raspberry Pi 5
========================================
=== Khởi tạo IoT Client ===
Khởi tạo GPIO controller...
Khởi tạo camera...
Khởi tạo audio...
✓ Tất cả components đã được khởi tạo
=== Bắt đầu IoT Client ===
Bắt đầu camera capture...
Bắt đầu audio recording...
Bắt đầu audio playback...
Bắt đầu WebSocket client...
Connected to WebSocket server
```

## 🔄 Cài đặt như systemd service (Tự động chạy khi Pi khởi động)

```bash
# SSH vào Pi
ssh pi@raspberry.local

cd /home/pi/IoT-Nha-Thong-Minh/raspberry-pi

# Install service
sudo ./scripts/install-service.sh

# Kiểm tra status
sudo systemctl status iot-client

# Xem logs
sudo journalctl -u iot-client -f
```

**Quản lý service:**
```bash
# Start
sudo systemctl start iot-client

# Stop
sudo systemctl stop iot-client

# Restart
sudo systemctl restart iot-client

# Disable auto-start
sudo systemctl disable iot-client

# Enable auto-start
sudo systemctl enable iot-client
```

## 🐛 Troubleshooting

### SSH không kết nối được

```bash
# Thử ping Pi
ping raspberry.local
# hoặc
ping 169.254.165.225

# Nếu không ping được → Kiểm tra network
```

**Enable SSH trên Pi:**
1. Kết nối Pi với màn hình và bàn phím
2. Chạy: `sudo raspi-config`
3. Interface Options → SSH → Enable

### Camera không hoạt động

```bash
# Kiểm tra camera được detect
v4l2-ctl --list-devices

# Test camera
libcamera-hello

# Kiểm tra permissions
sudo usermod -a -G video $USER
```

### GPIO không hoạt động

```bash
# Cài đặt lại gpiozero
pip uninstall gpiozero lgpio
pip install gpiozero lgpio

# Kiểm tra permissions
sudo usermod -a -G gpio $USER

# Logout và login lại
```

### Audio không hoạt động

```bash
# List audio devices
arecord -l  # Microphones
aplay -l    # Speakers

# Test microphone
arecord -d 5 test.wav
aplay test.wav
```

### WebSocket không kết nối

1. **Kiểm tra backend đang chạy:**
   ```bash
   # Trên máy backend
   curl http://localhost:8000/health
   ```

2. **Kiểm tra firewall:**
   ```bash
   # Allow port 8000
   sudo ufw allow 8000
   ```

3. **Kiểm tra URL trong config:**
   ```bash
   cat config/.env | grep WEBSOCKET_SERVER_URL
   # Phải là IP thật, không phải localhost!
   ```

## 📝 Update code sau khi sửa

Khi bạn sửa code trên máy dev:

```bash
# Cách 1: Dùng deploy script
cd raspberry-pi
./scripts/deploy-to-pi.sh

# Cách 2: Rsync thủ công
rsync -avz --exclude '.git' --exclude 'venv' \
    ./ pi@raspberry.local:/home/pi/IoT-Nha-Thong-Minh/raspberry-pi/

# Restart service trên Pi
ssh pi@raspberry.local "sudo systemctl restart iot-client"
```

## 🧪 Test từng component

### Test GPIO (LED):

```bash
# SSH vào Pi
ssh pi@raspberry.local

cd /home/pi/IoT-Nha-Thong-Minh/raspberry-pi
source venv/bin/activate

# Test LED
python3 << 'EOF'
from src.gpio_devices import GPIODevicesController, GPIODeviceConfig, DeviceType
import time

devices = {
    "LED Test": GPIODeviceConfig(
        gpio_pin=17,
        name="LED Test",
        device_type=DeviceType.LED
    )
}

gpio = GPIODevicesController(devices, mock_mode=False)
gpio.led_on("LED Test")
print("LED should be ON now!")
time.sleep(2)
gpio.led_off("LED Test")
print("LED should be OFF now!")
gpio.cleanup()
EOF
```

### Test Camera:

```bash
# Test OpenCV
python3 << 'EOF'
import cv2

cap = cv2.VideoCapture(0)
if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        print(f"✅ Camera OK! Frame size: {frame.shape}")
    else:
        print("❌ Cannot read frame")
else:
    print("❌ Cannot open camera")
cap.release()
EOF
```

### Test Audio:

```bash
# Test recording
python3 << 'EOF'
import pyaudio
import wave

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

p = pyaudio.PyAudio()

print("Recording 3 seconds...")
stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
frames = []

for i in range(0, int(RATE / CHUNK * 3)):
    data = stream.read(CHUNK)
    frames.append(data)

stream.stop_stream()
stream.close()
p.terminate()

wf = wave.open("test.wav", 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(p.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames))
wf.close()

print("✅ Recording saved to test.wav")
print("Play with: aplay test.wav")
EOF
```

## ✅ Checklist trước khi chạy production

- [ ] Backend server đang chạy và accessible
- [ ] Đã config đúng WebSocket URL trong `.env`
- [ ] Camera được detect (v4l2-ctl --list-devices)
- [ ] GPIO đã wiring đúng theo WIRING_SIMPLE.md
- [ ] Audio devices hoạt động (arecord -l, aplay -l)
- [ ] Test từng component một
- [ ] Đã cài systemd service cho auto-start
- [ ] Đã test restart Pi → service tự động chạy

## 🎯 Quick Commands Reference

```bash
# Deploy
./scripts/deploy-to-pi.sh

# SSH vào Pi
ssh pi@raspberry.local

# Chạy manual
cd /home/pi/IoT-Nha-Thong-Minh/raspberry-pi
source venv/bin/activate
python src/iot_client.py

# Xem logs service
sudo journalctl -u iot-client -f

# Restart service
sudo systemctl restart iot-client

# Test camera
v4l2-ctl --list-devices

# Test GPIO
gpio readall
```

---

**Happy deploying!** 🚀

Nếu gặp vấn đề, check logs và troubleshooting section ở trên.
