# Quick Start Guide - IoT Client

Hướng dẫn nhanh để chạy IoT Client trên Raspberry Pi 5.

## 🚀 Chạy với Docker (5 phút)

### Bước 1: Cài Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# Logout/login lại
```

### Bước 2: Clone repo

```bash
cd /home/pi
git clone <repo-url> IoT-Nha-Thong-Minh
cd IoT-Nha-Thong-Minh/raspberry-pi
```

### Bước 3: Cấu hình

```bash
cp config/.env.example config/.env
nano config/.env
```

Đổi dòng:
```bash
BACKEND_URL=ws://192.168.1.100:8000/ws/gemini
```
(Thay `192.168.1.100` bằng IP của backend server)

### Bước 4: Chạy

```bash
# Build
./scripts/docker-build.sh

# Run
./scripts/docker-run.sh

# Xem logs
docker-compose logs -f
```

**Done!** 🎉

---

## 🧪 Test với Mock Mode (không cần hardware)

```bash
./scripts/docker-mock.sh
```

Mock mode:
- ✅ Chạy trên bất kỳ máy nào (Mac/Windows/Linux/Pi)
- ✅ Không cần GPIO, camera, audio thật
- ✅ Test logic và WebSocket connection
- ✅ Hoàn hảo cho development

---

## 📋 Các lệnh thường dùng

```bash
# Xem logs
docker-compose logs -f

# Restart
docker-compose restart

# Dừng
docker-compose stop

# Xóa container
docker-compose down

# Rebuild sau khi sửa code
docker-compose up -d --build

# Check status
docker-compose ps
```

---

## 🔧 Kết nối Hardware

### GPIO (Relay Module)

```
Raspberry Pi          Relay Module
─────────────         ────────────
Pin 2 (5V)     ──►   VCC
Pin 6 (GND)    ──►   GND
Pin 11 (GPIO17)──►   IN1  [Phòng khách]
Pin 13 (GPIO27)──►   IN2  [Phòng ngủ]
Pin 15 (GPIO22)──►   IN3  [Nhà bếp]
Pin 16 (GPIO23)──►   IN4  [Ban công]
```

### USB Devices

- **Webcam** → USB 3.0 port (màu xanh)
- **Microphone** → USB port bất kỳ
- **Speaker** → 3.5mm jack hoặc USB

---

## ❓ Troubleshooting

### Container không start

```bash
docker-compose logs
```

### GPIO không hoạt động

Kiểm tra devices:
```bash
docker-compose exec iot-client ls -l /dev/gpio*
```

### Camera không thấy

```bash
# Trên host Pi
v4l2-ctl --list-devices

# Trong container
docker-compose exec iot-client v4l2-ctl --list-devices
```

### Audio không hoạt động

```bash
# Trên host Pi
aplay -l
arecord -l
```

---

## 📚 Tài liệu đầy đủ

- [README.md](README.md) - Hướng dẫn đầy đủ
- [DOCKER.md](DOCKER.md) - Chi tiết Docker setup
- [HARDWARE.md](HARDWARE.md) - Hướng dẫn lắp ráp hardware

---

## 🆘 Support

Nếu gặp vấn đề:

1. Check logs: `docker-compose logs -f`
2. Check hardware connections
3. Check config file: `cat config/.env`
4. Thử mock mode: `./scripts/docker-mock.sh`

---

## ⚡ Tips

**Development:**
```bash
# Edit code trên máy khác, sync qua git
git pull
docker-compose up -d --build
```

**Production:**
```bash
# Auto-restart enabled by default
# Container tự động restart khi:
# - Crash
# - Pi reboot
```

**Monitor:**
```bash
# CPU/Memory usage
docker stats iot-smart-home-client
```

---

Enjoy! 🎉
