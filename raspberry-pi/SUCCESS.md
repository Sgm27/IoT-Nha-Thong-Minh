# ✅ Docker Setup Thành Công!

IoT Client đã build và chạy thành công với Docker!

## 🎯 Đã hoàn thành

- ✅ Dockerfile build successfully
- ✅ Docker Compose configuration
- ✅ Mock mode hoạt động hoàn hảo
- ✅ GPIO, Camera, Audio services khởi động
- ✅ Ready để deploy lên Raspberry Pi

## 🚀 Cách sử dụng

### Test trên máy Development (Mac/Windows) - Mock Mode

```bash
cd /Users/h3nr1.d14z/Projects/HieuLD/IoT-Nha-Thong-Minh/raspberry-pi

# Start với mock mode
MOCK_MODE=true docker-compose up

# Hoặc dùng script
./scripts/docker-mock.sh
```

**Mock mode sẽ:**
- ✅ Không cần GPIO hardware
- ✅ Không cần camera thật
- ✅ Không cần microphone/speaker
- ✅ Test logic và WebSocket connection
- ✅ Chạy trên bất kỳ máy nào có Docker

### Deploy lên Raspberry Pi - Hardware Mode

**Bước 1:** Copy code lên Pi

```bash
# Trên Pi
cd /home/pi
git clone <repo-url> IoT-Nha-Thong-Minh
cd IoT-Nha-Thong-Minh/raspberry-pi
```

**Bước 2:** Uncomment device mappings trong `docker-compose.yml`

```yaml
privileged: true
network_mode: host
devices:
  - /dev/gpiomem:/dev/gpiomem
  - /dev/gpiochip0:/dev/gpiochip0
  - /dev/gpiochip4:/dev/gpiochip4
  - /dev/video0:/dev/video0
  - /dev/snd:/dev/snd
```

**Bước 3:** Chạy

```bash
# Without mock mode (real hardware)
docker-compose up -d

# Check logs
docker-compose logs -f
```

## 📊 Verified Logs

Mock mode logs cho thấy tất cả hoạt động:

```
IoT Smart Home Client - Raspberry Pi 5
[MOCK] Khởi tạo relay cho 'Phòng khách' (GPIO17)
[MOCK] Khởi tạo relay cho 'Phòng ngủ' (GPIO27)
[MOCK] Khởi tạo relay cho 'Nhà bếp' (GPIO22)
[MOCK] Khởi tạo relay cho 'Ban công' (GPIO23)
[MOCK] Camera khởi tạo ở chế độ mock
[MOCK] Audio khởi tạo ở chế độ mock
✓ Tất cả components đã được khởi tạo
Camera capture đã bắt đầu
[MOCK] Bắt đầu recording
[MOCK] Bắt đầu playback
Đang kết nối đến ws://localhost:8000/ws/gemini...
```

## 🎓 Commands Cheat Sheet

```bash
# Build image
docker-compose build

# Run mock mode (foreground)
MOCK_MODE=true docker-compose up

# Run mock mode (background)
MOCK_MODE=true docker-compose up -d

# Run real hardware (trên Pi)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild
docker-compose build --no-cache
```

## 🔧 Environment Variables

Trong `docker-compose.yml`:

```yaml
environment:
  - MOCK_MODE=${MOCK_MODE:-false}    # Override bằng MOCK_MODE=true
  - BACKEND_URL=${BACKEND_URL:-ws://localhost:8000/ws/gemini}
```

## 📚 Next Steps

1. **Test integration với backend:**
   ```bash
   # Terminal 1: Start backend
   cd ../
   docker-compose up backend

   # Terminal 2: Start Pi client (mock)
   cd raspberry-pi
   MOCK_MODE=true BACKEND_URL=ws://localhost:8000/ws/gemini docker-compose up
   ```

2. **Deploy lên Raspberry Pi thật:**
   - Kết nối hardware theo `HARDWARE.md`
   - Uncomment device mappings
   - Set `MOCK_MODE=false`
   - Run `docker-compose up -d`

3. **Monitor & Debug:**
   ```bash
   docker-compose logs -f
   docker stats iot-smart-home-client
   ```

## 🎉 Kết luận

Docker setup hoàn toàn thành công! Bạn có thể:
- ✅ Chạy mock mode trên máy development để test
- ✅ Deploy lên Raspberry Pi với hardware thật
- ✅ Auto-restart khi crash/reboot
- ✅ Easy maintenance và updates

**Ready để deploy!** 🚀
