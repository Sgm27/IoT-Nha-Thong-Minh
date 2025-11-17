# Docker Compose - Hướng dẫn sử dụng

Hướng dẫn chạy các services trong project với Docker Compose.

## Tổng quan Services

Project có 3 services chính:

1. **Backend** - FastAPI server (port 8000)
2. **Frontend** - React web app (port 5173)
3. **Raspberry Pi Client** - IoT client (chỉ chạy trên Pi)

## Chạy trên máy Development (Mac/Windows/Linux)

### Chỉ Backend + Frontend

```bash
# Từ thư mục root
docker-compose up -d

# Hoặc
docker-compose up -d backend frontend
```

Services sẽ chạy:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173

### Backend + Frontend + Raspberry Pi Client (Mock Mode)

Để test toàn bộ hệ thống, bao gồm IoT client ở mock mode:

```bash
docker-compose --profile raspberry-pi up -d
```

Raspberry Pi client sẽ chạy ở **mock mode**:
- Không cần GPIO, camera, audio thật
- Kết nối với backend qua WebSocket
- Hữu ích để test integration

### Xem logs

```bash
# Tất cả services
docker-compose logs -f

# Một service cụ thể
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f raspberry-pi
```

## Chạy trên Raspberry Pi

### Option 1: Chạy toàn bộ stack

Trên Raspberry Pi, uncomment các device mappings trong `docker-compose.yml`:

```yaml
raspberry-pi:
  privileged: true          # Uncomment
  network_mode: host        # Uncomment
  devices:                  # Uncomment toàn bộ
    - /dev/gpiomem:/dev/gpiomem
    - /dev/gpiochip0:/dev/gpiochip0
    - /dev/gpiochip4:/dev/gpiochip4
    - /dev/video0:/dev/video0
    - /dev/snd:/dev/snd
  environment:
    - MOCK_MODE=false       # Đổi thành false
```

Sau đó:

```bash
# Chạy tất cả (backend, frontend, raspberry-pi)
docker-compose --profile raspberry-pi up -d
```

### Option 2: Chỉ chạy IoT Client (Khuyến nghị)

Nếu backend + frontend chạy ở server khác, chỉ cần chạy IoT client trên Pi:

```bash
cd raspberry-pi
docker-compose up -d
```

File `raspberry-pi/docker-compose.yml` đã được config sẵn cho Pi.

## Các lệnh thường dùng

### Start/Stop

```bash
# Start tất cả (không có raspberry-pi)
docker-compose up -d

# Start với raspberry-pi
docker-compose --profile raspberry-pi up -d

# Stop tất cả
docker-compose stop

# Stop một service
docker-compose stop backend
```

### Rebuild

```bash
# Rebuild tất cả
docker-compose build

# Rebuild một service
docker-compose build backend

# Rebuild và restart
docker-compose up -d --build
```

### Cleanup

```bash
# Stop và xóa containers
docker-compose down

# Xóa cả volumes
docker-compose down -v
```

### Logs & Debug

```bash
# Logs realtime
docker-compose logs -f

# Logs của một service
docker-compose logs -f backend

# 100 dòng cuối
docker-compose logs --tail=100

# Shell vào container
docker-compose exec backend bash
docker-compose exec frontend sh
docker-compose exec raspberry-pi bash
```

### Status & Monitor

```bash
# Check status
docker-compose ps

# Resource usage
docker stats
```

## Environment Variables

### Backend

File: `backend/.env`

```bash
GOOGLE_API_KEY=your-api-key
GEMINI_MODEL=gemini-live-2.5-flash-preview
```

### Raspberry Pi Client

File: `raspberry-pi/config/.env`

```bash
# Khi chạy cùng stack
BACKEND_URL=ws://backend:8000/ws/gemini

# Khi backend ở server riêng
BACKEND_URL=ws://192.168.1.100:8000/ws/gemini

# Mock mode
MOCK_MODE=false  # true cho mock, false cho hardware thật
```

## Profiles Explained

Docker Compose profiles cho phép bật/tắt services:

```bash
# Không có profile = chỉ backend + frontend
docker-compose up -d

# Với profile raspberry-pi = tất cả services
docker-compose --profile raspberry-pi up -d

# Chỉ backend
docker-compose up -d backend

# Chỉ frontend (cần backend running)
docker-compose up -d backend frontend
```

## Network Configuration

### Default Network (Bridge)

Services giao tiếp qua service names:
- `http://backend:8000` - Từ frontend hoặc raspberry-pi
- `http://frontend:80` - Từ backend

### Host Network (Raspberry Pi)

Khi dùng `network_mode: host` trên Pi:
- Service dùng network của host
- Access backend: `ws://localhost:8000` (nếu backend cũng trên Pi)
- Hoặc: `ws://192.168.1.x:8000` (nếu backend ở server khác)

## Troubleshooting

### Backend không start

```bash
# Check logs
docker-compose logs backend

# Check nếu thiếu .env
ls backend/.env

# Rebuild
docker-compose build backend
docker-compose up -d backend
```

### Frontend không connect backend

```bash
# Check backend có chạy không
docker-compose ps

# Check network
docker-compose exec frontend ping backend

# Check logs
docker-compose logs frontend
```

### Raspberry Pi client không kết nối

```bash
# Check BACKEND_URL
cat raspberry-pi/config/.env

# Check logs
docker-compose logs raspberry-pi

# Test WebSocket từ trong container
docker-compose exec raspberry-pi python -c "
import asyncio
import websockets

async def test():
    async with websockets.connect('ws://backend:8000/ws/gemini') as ws:
        print('Connected!')

asyncio.run(test())
"
```

### Port conflicts

Nếu port 8000 hoặc 5173 đã được dùng:

```bash
# Đổi port trong docker-compose.yml
services:
  backend:
    ports:
      - "8001:8000"  # Host port 8001

  frontend:
    ports:
      - "3000:80"    # Host port 3000
```

### Permission issues (Raspberry Pi)

```bash
# Nếu không access được devices
sudo docker-compose --profile raspberry-pi up -d

# Hoặc thêm user vào docker group
sudo usermod -aG docker $USER
# Logout/login lại
```

## Development Workflow

### Frontend Development

```bash
# Start backend
docker-compose up -d backend

# Develop frontend natively (hot reload)
cd frontend
npm run dev

# Hoặc dùng Docker với code mounting
# (Thêm volume mount trong docker-compose.yml)
```

### Backend Development

```bash
# Develop natively
cd backend
uvicorn app.main:create_app --reload

# Hoặc Docker với auto-reload
# (Thêm volume mount cho code)
```

### Raspberry Pi Client Development

```bash
# Mock mode để test logic
cd raspberry-pi
MOCK_MODE=true docker-compose up

# Hoặc test natively
cd raspberry-pi
source .venv/bin/activate
MOCK_MODE=true python src/iot_client.py
```

## Production Deployment

### Trên Cloud/VPS (Backend + Frontend)

```bash
# Build production images
docker-compose build

# Run in background
docker-compose up -d

# Enable auto-restart
# (Đã có restart: unless-stopped trong config)

# Setup reverse proxy (nginx/traefik) nếu cần
```

### Trên Raspberry Pi (IoT Client)

```bash
cd raspberry-pi

# Edit config
nano config/.env

# Run
docker-compose up -d

# Check logs
docker-compose logs -f
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│              Development Machine                 │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Backend  │  │ Frontend │  │ Raspberry Pi │  │
│  │ :8000    │◄─┤ :5173    │  │ (Mock Mode)  │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│              Production Setup                    │
│                                                  │
│  Cloud/VPS:                 Raspberry Pi:        │
│  ┌──────────┐  ┌──────────┐                     │
│  │ Backend  │  │ Frontend │                     │
│  │ :8000    │◄─┤ :5173    │                     │
│  └────┬─────┘  └──────────┘                     │
│       │                                          │
│       └──────────► WebSocket ◄────┐             │
│                                    │             │
│                    ┌───────────────┴──────────┐  │
│                    │  Raspberry Pi IoT Client │  │
│                    │  - GPIO Control          │  │
│                    │  - Camera Streaming      │  │
│                    │  - Audio I/O             │  │
│                    └──────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## Quick Reference

| Command | Description |
|---------|-------------|
| `docker-compose up -d` | Start backend + frontend |
| `docker-compose --profile raspberry-pi up -d` | Start all services |
| `docker-compose logs -f` | View all logs |
| `docker-compose stop` | Stop all services |
| `docker-compose down` | Stop and remove containers |
| `docker-compose build` | Rebuild images |
| `docker-compose ps` | Check status |
| `docker-compose exec <service> bash` | Shell into container |

## Kết luận

- **Development**: Chạy backend + frontend trên máy dev, dùng mock mode cho Pi client
- **Production**: Backend + frontend trên cloud/VPS, Pi client trên Raspberry Pi thật
- **Testing**: Dùng profiles và mock mode để test integration mà không cần hardware
