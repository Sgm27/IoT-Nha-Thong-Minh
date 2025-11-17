# Docker Setup cho IoT Client

Hướng dẫn chạy IoT Client với Docker trên Raspberry Pi 5.

## Tại sao dùng Docker?

✅ **Ưu điểm:**
- Dễ deploy - chỉ cần Docker, không lo dependencies
- Isolated environment - không ảnh hưởng system packages
- Portable - chạy trên bất kỳ Pi nào có Docker
- Auto-restart - container tự động restart khi crash hoặc reboot
- Dễ update - chỉ cần rebuild image

⚠️ **Lưu ý:**
- Cần privileged mode để access GPIO (giảm security)
- Build image lần đầu mất ~10-15 phút trên Pi
- Image size ~500MB-1GB

## GPIO trong Docker - CÓ THỂ HOẠT ĐỘNG!

Docker **CÓ THỂ** access GPIO, camera, và audio nếu:
1. Chạy với `privileged: true` HOẶC
2. Map đúng devices (`/dev/gpiomem`, `/dev/video*`, `/dev/snd`)
3. Grant các capabilities cần thiết

**Mock mode** vẫn hoạt động bình thường trong Docker mà không cần hardware.

## Cài đặt Docker trên Raspberry Pi

### 1. Cài Docker

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group (để chạy docker không cần sudo)
sudo usermod -aG docker $USER

# Logout/login lại để group có hiệu lực
```

### 2. Cài Docker Compose

```bash
# Docker Compose đã được included trong Docker mới
# Kiểm tra:
docker compose version

# Nếu chưa có, cài thêm:
sudo apt-get install docker-compose-plugin
```

### 3. Verify installation

```bash
docker --version
docker compose version
```

## Quick Start

### 1. Clone repository

```bash
cd /home/pi
git clone <repo-url> IoT-Nha-Thong-Minh
cd IoT-Nha-Thong-Minh/raspberry-pi
```

### 2. Cấu hình

```bash
# Tạo config file
cp config/.env.example config/.env

# Chỉnh sửa config
nano config/.env
```

**Quan trọng:** Đổi `BACKEND_URL` thành địa chỉ backend server:
```bash
BACKEND_URL=ws://192.168.1.100:8000/ws/gemini
```

### 3. Build image

```bash
./scripts/docker-build.sh
```

Hoặc manual:
```bash
docker build -t iot-smart-home-client:latest .
```

### 4. Chạy container

```bash
./scripts/docker-run.sh
```

Hoặc manual:
```bash
docker-compose up -d
```

### 5. Xem logs

```bash
docker-compose logs -f
```

## Mock Mode - Test không cần Hardware

Để test IoT client mà không cần kết nối GPIO, camera, audio thật:

```bash
# Chạy mock mode
./scripts/docker-mock.sh
```

Hoặc:
```bash
MOCK_MODE=true docker-compose up
```

Ở mock mode:
- GPIO chỉ log actions, không điều khiển pins thật
- Camera tạo frames đen có timestamp
- Audio không capture/playback thật
- WebSocket vẫn kết nối bình thường với backend

**Use cases:**
- Test trên máy development (Mac/Windows/Linux)
- Kiểm tra logic trước khi deploy lên Pi
- Debug WebSocket communication
- CI/CD testing

## Docker Compose Commands

### Basic commands

```bash
# Start container (background)
docker-compose up -d

# Start container (foreground, xem logs trực tiếp)
docker-compose up

# Stop container
docker-compose stop

# Restart container
docker-compose restart

# Stop và remove container
docker-compose down

# Remove container + volumes
docker-compose down -v
```

### Logs và monitoring

```bash
# Xem logs realtime
docker-compose logs -f

# Xem logs của 100 dòng cuối
docker-compose logs --tail=100

# Xem logs từ 10 phút trước
docker-compose logs --since 10m

# Check container status
docker-compose ps

# Check resource usage
docker stats iot-smart-home-client
```

### Rebuild và update

```bash
# Rebuild image sau khi thay đổi code
docker-compose build

# Rebuild và restart
docker-compose up -d --build

# Pull latest image và restart
docker-compose pull
docker-compose up -d
```

### Exec commands trong container

```bash
# Shell vào container
docker-compose exec iot-client bash

# Chạy Python trong container
docker-compose exec iot-client python -c "import cv2; print(cv2.__version__)"

# Check GPIO devices
docker-compose exec iot-client ls -l /dev/gpio*

# Check camera devices
docker-compose exec iot-client v4l2-ctl --list-devices
```

## Cấu trúc Docker Setup

### Dockerfile

Multi-stage build để giảm image size:

```dockerfile
# Stage 1: Builder - compile dependencies
FROM python:3.11-slim-bookworm AS builder
RUN pip install -r requirements.txt

# Stage 2: Runtime - copy compiled packages
FROM python:3.11-slim-bookworm
COPY --from=builder /opt/venv /opt/venv
```

### docker-compose.yml

```yaml
services:
  iot-client:
    privileged: true       # Access GPIO/devices
    network_mode: host     # WebSocket hoạt động tốt
    devices:               # Device mappings
      - /dev/gpiomem:/dev/gpiomem
      - /dev/video0:/dev/video0
      - /dev/snd:/dev/snd
    volumes:
      - ./config/.env:/app/config/.env
    restart: unless-stopped
```

## Device Mappings Explained

### GPIO Devices

```yaml
devices:
  - /dev/gpiomem:/dev/gpiomem    # GPIO memory access (non-root)
  - /dev/gpiochip0:/dev/gpiochip0  # GPIO chip 0
  - /dev/gpiochip4:/dev/gpiochip4  # GPIO chip 4 (Pi 5)
```

Raspberry Pi 5 có 2 GPIO chips (gpiochip0 và gpiochip4).

### Camera Devices

```yaml
devices:
  - /dev/video0:/dev/video0  # USB webcam
  # - /dev/video1:/dev/video1  # Nếu có nhiều cameras
```

Kiểm tra video devices:
```bash
v4l2-ctl --list-devices
ls -l /dev/video*
```

### Audio Devices

```yaml
devices:
  - /dev/snd:/dev/snd  # Tất cả ALSA sound devices
```

## Privileged Mode vs Device Mapping

### Option 1: Privileged Mode (Đơn giản nhưng kém security)

```yaml
services:
  iot-client:
    privileged: true
```

✅ Pros: Đơn giản, access tất cả devices
❌ Cons: Container có full access vào host (security risk)

### Option 2: Device Mapping (An toàn hơn)

```yaml
services:
  iot-client:
    devices:
      - /dev/gpiomem:/dev/gpiomem
      - /dev/video0:/dev/video0
      - /dev/snd:/dev/snd
    cap_add:
      - SYS_RAWIO
```

✅ Pros: Chỉ grant access cần thiết
❌ Cons: Phức tạp hơn, dễ thiếu permissions

**Khuyến nghị:** Dùng privileged mode trên Pi cá nhân, dùng device mapping cho production.

## Network Mode

### host network (Khuyến nghị)

```yaml
network_mode: host
```

✅ WebSocket hoạt động tốt
✅ Không cần port mapping
✅ Performance tốt hơn
❌ Không isolated network

### bridge network

```yaml
ports:
  - "8080:8080"  # Nếu cần expose ports
```

✅ Isolated network
❌ Phức tạp hơn với WebSocket

## Volume Mappings

```yaml
volumes:
  # Config file (read-write)
  - ./config/.env:/app/config/.env:rw

  # Logs (persistent)
  - iot-logs:/var/log

  # Development mode: Mount code để live reload
  - ./src:/app/src:ro
```

## Troubleshooting

### Container không start

```bash
# Xem logs lỗi
docker-compose logs

# Check container status
docker-compose ps

# Inspect container
docker inspect iot-smart-home-client
```

### GPIO không hoạt động

```bash
# Check device có được mount không
docker-compose exec iot-client ls -l /dev/gpio*

# Check permissions
docker-compose exec iot-client cat /proc/self/status | grep CapEff
```

### Camera không hoạt động

```bash
# List video devices trong container
docker-compose exec iot-client v4l2-ctl --list-devices

# Test camera
docker-compose exec iot-client python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAIL')"
```

### Audio không hoạt động

```bash
# Check audio devices
docker-compose exec iot-client aplay -l
docker-compose exec iot-client arecord -l

# Test audio
docker-compose exec iot-client speaker-test -t wav -c 2
```

### WebSocket không kết nối

```bash
# Check network
docker-compose exec iot-client ping <backend-ip>

# Test WebSocket từ trong container
docker-compose exec iot-client python -c "
import websockets
import asyncio
async def test():
    async with websockets.connect('ws://192.168.1.100:8000/ws/gemini') as ws:
        print('Connected!')
asyncio.run(test())
"
```

### Container chiếm nhiều resources

```bash
# Check resource usage
docker stats iot-smart-home-client

# Limit resources
```

Thêm vào `docker-compose.yml`:
```yaml
services:
  iot-client:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          memory: 512M
```

## Auto-start on Boot

Docker Compose container với `restart: unless-stopped` sẽ tự động start khi Pi reboot.

Verify:
```bash
# Check restart policy
docker inspect iot-smart-home-client | grep -A 5 RestartPolicy
```

Nếu muốn disable auto-restart:
```bash
docker update --restart=no iot-smart-home-client
```

## Update và Maintenance

### Update code

```bash
# Pull latest code
git pull

# Rebuild và restart
docker-compose up -d --build
```

### Update dependencies

1. Chỉnh sửa `requirements.txt`
2. Rebuild image:
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Cleanup

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Remove everything unused
docker system prune -a
```

## Production Checklist

Trước khi deploy production:

- [ ] Đã test với mock mode
- [ ] Đã test với hardware thật
- [ ] Đã cấu hình `config/.env` đúng
- [ ] Đã set `restart: unless-stopped`
- [ ] Đã test auto-restart (reboot Pi)
- [ ] Đã set resource limits nếu cần
- [ ] Đã setup log rotation
- [ ] Đã backup config files

## So sánh: Docker vs Native

| Feature | Docker | Native |
|---------|--------|--------|
| Setup | Dễ (chỉ cần Docker) | Khó hơn (nhiều dependencies) |
| Portable | ✅ Cao | ❌ Thấp |
| Performance | Good (~5% overhead) | Excellent |
| Security | Có thể isolated | Chạy trực tiếp |
| Auto-restart | ✅ Built-in | Cần systemd service |
| Update | Rebuild image | Update packages |
| Debugging | Phức tạp hơn | Dễ hơn |

**Khuyến nghị:**
- **Docker**: Cho production, dễ deploy và maintain
- **Native**: Cho development, debugging chi tiết

## Tips

1. **Development với Docker:**
   - Mount source code: `- ./src:/app/src:ro`
   - Restart container sau khi thay đổi code
   - Hoặc dùng auto-reload tools

2. **Logging:**
   - Logs được lưu trong Docker volume
   - Access: `docker-compose logs -f`
   - Hoặc mount `/var/log` ra host

3. **Debugging:**
   - Shell vào container: `docker-compose exec iot-client bash`
   - Check processes: `docker-compose top`
   - Inspect: `docker inspect iot-smart-home-client`

4. **Performance:**
   - Limit resources nếu Pi chạy nhiều services
   - Monitor với `docker stats`
   - Consider native install nếu cần max performance

## Kết luận

Docker setup cho IoT client hoàn toàn khả thi và có nhiều ưu điểm:
- ✅ **GPIO hoạt động** với privileged mode hoặc device mapping
- ✅ **Mock mode** cho development và testing
- ✅ **Easy deployment** - chỉ cần Docker
- ✅ **Auto-restart** khi crash hoặc reboot
- ✅ **Portable** - chạy trên bất kỳ Pi nào

Tuy nhiên cần lưu ý về security (privileged mode) và có một chút overhead so với native install.
