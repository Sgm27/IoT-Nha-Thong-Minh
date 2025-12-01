# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IoT Smart Home System - A full-stack voice-controlled smart home platform integrating Google's Gemini Live API, real-time fire detection, and IoT device control. Designed to run on Raspberry Pi with camera, microphone, speaker, and relay modules.

**Primary Language**: Vietnamese (all user-facing text and system instructions)

**Tech Stack**:
- Backend: FastAPI + Python (Gemini Live, fire detection, smart home services)
- Frontend: React + TypeScript + Vite (WebSocket client, voice/camera streaming)
- Android: Kotlin-based mobile app
- Infrastructure: Docker Compose, Nginx reverse proxy

## Quick Start

### Docker (Recommended)
```bash
# Start all services
docker-compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

### Local Development
```bash
# Start both backend and frontend
./start.sh

# Or run individually:

# Backend (from project root)
cd backend
uvicorn app.main:create_app --reload --host 0.0.0.0 --port 8000

# Frontend (from project root)
cd frontend
npm run dev
```

### Environment Setup
1. Copy `backend/.env.example` to `backend/.env`
2. Set `GOOGLE_API_KEY` (required for Gemini Live integration)
3. Optional: Configure fire detection parameters, file paths, music settings

## System Architecture

### High-Level Design

This is a **monolithic full-duplex real-time communication system** where:

1. **Frontend** streams voice (microphone) + video (camera) → Gemini via backend WebSocket
2. **Backend** orchestrates:
   - Gemini Live API bidirectional streaming (audio, text, tool calls)
   - OpenCV fire detection on camera frames
   - Smart home state management (lights, music)
   - Session persistence for Gemini conversation context
3. **Gemini** processes multimodal input and can invoke smart home tools
4. **Hardware** (Raspberry Pi GPIO) controls physical devices through relay modules

### Critical Data Flows

**Voice Control Flow**:
```
Microphone → AudioWorklet (16kHz PCM) → WebSocket → Backend → Gemini Live
Gemini Live → Audio Response → WebSocket → Audio Queue → Speakers
```

**Fire Detection Flow**:
```
Camera → Canvas Capture (JPEG) → WebSocket → Backend → OpenCV Detection
Fire Detected → Voice Alert Generation → Audio Base64 → WebSocket → Speakers
```

**Smart Home Control Flow**:
```
Gemini Tool Call → LightingService/MusicService → GPIO/File System
State Change → Observer Notification → WebSocket → Frontend UI Update
```

### Three-Tier Architecture

**1. Backend (FastAPI - Python)**

Location: `backend/`

Core Services (`app/services/`):
- `gemini_service.py` - **Primary orchestrator**; manages Gemini Live WebSocket, handles tool calls, coordinates audio/text/image streams
- `smart_home_service.py` - State manager for `LightingService` (GPIO relays) and `MusicService` (file playback)
- `fire_detection_service.py` - Wraps OpenCV fire detector with alert throttling
- `session_service.py` - Persists Gemini session handles for conversation resumption
- `notification_voice_service.py` - TTS for fire alerts and notifications

API Routes (`app/api/routes/`):
- `websocket.py` - Main Gemini WebSocket endpoint (`/ws/gemini`)
- `smart_home.py` - REST + WebSocket for lights and music (`/smart-home/*`)
- `assistant.py` - Additional assistant endpoints

**2. Frontend (React + TypeScript)**

Location: `frontend/`

Custom Hooks (`src/hooks/`) - All business logic:
- `useGeminiRealtime.ts` - **Primary orchestrator**; manages WebSocket, audio pipeline, camera streaming, message handling
- `useLights.ts` - Light state sync via WebSocket + REST control
- `useMusicController.ts` - Music playback with browser audio sync

UI Components (`src/components/`):
- `GeminiChatCard.tsx` - Chat interface with voice/camera controls
- `LightControlCard.tsx` - Light switch UI
- `MusicControlCard.tsx` - Music player UI
- `ui/` - shadcn/ui components (Button, Card, Input, etc.)

**3. Android App**

Location: `android-app/`
- Kotlin-based mobile client for smart home control
- Connects to backend REST APIs

## WebSocket Protocol

### Main Gemini WebSocket: `/ws/gemini`

**Client → Server:**
```json
{"text": "string"}
{"realtime_input": {"media_chunks": [{"mime_type": "audio/pcm;rate=16000", "data": "base64"}]}}
{"realtime_input": {"media_chunks": [{"mime_type": "image/jpeg", "data": "base64"}]}}
{"keepalive": {"timestamp": "ISO8601"}}
```

**Server → Client:**
```json
{"setupComplete": {...}}
{"audio": {"data": "base64", "mime_type": "audio/pcm", "sample_rate": 24000}}
{"text": "string"}
{"transcription": {"text": "...", "sender": "User|Gemini", "finished": bool}}
{"type": "smart_home_light_update", "location": "...", "is_on": bool}
{"type": "smart_home_music", "matched_song": "...", "stream_url": "..."}
{"type": "motor_control", "name": "Quạt", "action": "on|off|forward|backward|stop", "speed": 0.0-1.0}
{"type": "fire_detection_alert", "message": "...", "audio_base64": "..."}
```

### Smart Home WebSockets

- `/smart-home/lights/stream` - Real-time light state updates
- `/smart-home/music/updates` - Music playback state sync

## Key Technical Concepts

### 1. Gemini Live Integration

**Bidirectional Streaming** (`backend/app/services/gemini_service.py`):
- Three concurrent async tasks: client→Gemini relay, Gemini→client relay, keepalive ping
- Session resumption via persisted handles (token cost optimization)
- Function calling: Gemini can invoke `turn_on_light`, `turn_off_light`, `play_music`, `pause_music`, `continue_music`, `control_motor`

**Configuration**:
- Voice: "Aoede" (TTS voice name)
- Language: "vi-VN" (Vietnamese)
- Temperature: 0.6, Top-P: 0.85
- System instruction defines smart home context in Vietnamese

### 2. Audio Pipeline

**Input** (`frontend/src/hooks/useGeminiRealtime.ts`):
- Microphone → AudioContext → AudioWorkletNode (`pcm-worklet-processor.js`)
- Resampling: Browser sample rate → 16kHz PCM16 (Gemini requirement)
- 100ms chunks streamed via WebSocket

**Output**:
- Base64 PCM chunks from Gemini → AudioBuffer
- Queue management prevents overlap/stuttering
- Sample rate: 24kHz playback

**Utilities** (`frontend/src/lib/audio.ts`):
- `resampleFloat32()` - Linear interpolation resampling
- `float32ToPCM16()` - Format conversion
- `decodeAudioChunk()` - Base64 → AudioBuffer

### 3. Fire Detection

**Implementation** (`backend/app/utils/fire_detection.py`):
- OpenCV HSV color space filtering for flame detection
- Configurable `FireParams` (HSV ranges, contour area thresholds)
- Returns fire percentage, confidence, region count

**Service Layer** (`backend/app/services/fire_detection_service.py`):
- Alert cooldown mechanism (default 60s)
- Voice notification caching (TTS audio stored as base64)
- Camera frame interval configurable via `CAPTURE_INTERVAL_SECONDS`

### 4. Smart Home State Management

**LightingService** (`backend/app/services/smart_home_service.py`):
- Persists state to `data/light_state.json`
- Observer pattern for WebSocket real-time updates
- Default lights: Phòng khách, Phòng ngủ, Bếp
- **GPIO Integration**: Designed for relay module control (see ITEMS.md)
- `notify_motor_control()` broadcasts motor commands to all connected clients

**MusicService**:
- Fuzzy string matching (`SequenceMatcher`) for song search
- Threshold: `MUSIC_SIMILARITY_THRESHOLD` (0.72)
- Library location: `backend/music/` (MP3/WAV/FLAC)
- Two-way sync: Backend state ↔ Browser HTML5 Audio

**State Persistence** (`backend/data/`):
- `light_state.json` - Light states
- `conversation_history.json` - Full chat history
- `session_handle.json` - Gemini session + token usage
- `images/` - Optional captured frames

### 5. Camera Streaming

**Frontend** (`frontend/src/hooks/useGeminiRealtime.ts`):
- getUserMedia API (ideal: 720p)
- Canvas-based JPEG compression (quality: 0.75)
- Automatic downscaling (max 720px dimension)
- Configurable capture interval (server-controlled)
- Max size: 4MB per frame

## Common Development Tasks

### Adding a New Smart Home Device

1. **Backend** (`backend/app/services/smart_home_service.py`):
   - Add service class (similar to `LightingService`)
   - Implement state persistence and observer pattern

2. **Backend** (`backend/app/services/gemini_service.py`):
   - Add tool declaration in `_create_live_config()` tools array
   - Add handler in `_handle_tool_calls()`
   - Update `SYSTEM_INSTRUCTION` (in Vietnamese)

3. **Backend** (`backend/app/api/routes/smart_home.py`):
   - Add REST endpoints for direct control

4. **Frontend** (`frontend/src/hooks/`):
   - Create custom hook for WebSocket + REST integration

5. **Frontend** (`frontend/src/components/`):
   - Create UI component card

6. **Frontend** (`frontend/src/App.tsx`):
   - Import and wire up hook + component

### Modifying Fire Detection Sensitivity

Edit `backend/app/utils/fire_detection.py`:
```python
@dataclass
class FireParams:
    lower_hsv: tuple[int, int, int] = (0, 100, 100)   # Flame color range
    upper_hsv: tuple[int, int, int] = (40, 255, 255)
    min_contour_area: int = 500                       # Noise filter
    fire_percentage_threshold: float = 0.02           # Alert threshold
```

### Testing Without Gemini API Key

Backend enters **offline echo mode** when `GOOGLE_API_KEY` is not set:
- `gemini_service.py:_run_offline_loop()` echoes back messages
- Useful for testing WebSocket infrastructure, tool calls, smart home integration

## Hardware Integration (Raspberry Pi)

Required components (see `ITEMS.md` for complete shopping list):
- Raspberry Pi 5 with 5V-3A power supply
- Camera (CSI Module 3 or USB webcam)
- USB microphone
- Speaker (USB or 3.5mm)
- LEDs for room lights
- Buzzer for fire alerts
- L298N motor driver + DC motor (Motor 130) for fan control
- Jumper wires + GPIO breakout

**GPIO Mapping** (configure in `raspberry-pi/src/iot_client.py`):

| Device | GPIO Pin(s) | Notes |
|--------|-------------|-------|
| LED Phòng khách | GPIO17 | Active HIGH |
| LED Phòng ngủ | GPIO27 | Active HIGH |
| LED Bếp | GPIO22 | Active HIGH |
| Buzzer | GPIO23 | Fire alert |
| Motor (L298N) | GPIO16 (IN1), GPIO20 (IN2), GPIO18 (ENA) | DC motor speed control |

**Motor Wiring (L298N Driver)**:
```
Pi Pin 2 (5V)     → L298N 12V
Pi Pin 9 (GND)    → L298N GND
Pi Pin 12 (GPIO18)→ L298N ENA (remove jumper)
Pi Pin 36 (GPIO16)→ L298N IN1
Pi Pin 38 (GPIO20)→ L298N IN2
L298N OUT1/OUT2   → DC Motor wires
```

**Camera Setup**:
- CSI: Enable via `sudo raspi-config`, test with `libcamera-jpeg`
- USB: Verify with `lsusb`, test with `ffmpeg`

**Audio Setup**:
- Check devices: `arecord -l`, `aplay -l`
- Configure ALSA/PulseAudio for microphone + speaker

## Production Deployment

### Docker Multi-Stage Builds

**Backend** (`backend/Dockerfile`):
- Python 3.12 slim base
- Installs system deps for OpenCV
- Runs Uvicorn on port 8000

**Frontend** (`frontend/Dockerfile`):
- Build stage: Node 20 Alpine → npm build
- Production: nginx:1.25-alpine serves static files
- Nginx config proxies `/smart-home/*`, `/ws/*`, `/assistant/*` to backend

**Docker Compose** (`docker-compose.yml`):
- Backend: Port 8000, volumes for `data/` and `music/`
- Frontend: Port 5173 (nginx), depends on backend
- Both services auto-restart

### Nginx Reverse Proxy

Frontend `nginx.conf` configuration:
- Serves React SPA from `/usr/share/nginx/html`
- Proxies API requests to `http://backend:8000`
- WebSocket upgrade support for `/ws/*`
- SPA fallback: All routes serve `index.html`

## File Organization

```
IoT-Nha-Thong-Minh/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI factory
│   │   ├── core/
│   │   │   ├── config.py              # Environment config (Settings dataclass)
│   │   │   └── logging_config.py
│   │   ├── api/routes/                # HTTP & WebSocket endpoints
│   │   ├── services/                  # Business logic (Gemini, smart home, fire)
│   │   ├── utils/                     # Pure utilities (fire detection)
│   │   └── scripts/                   # One-off scripts (audio generation)
│   ├── data/                          # Runtime state (JSON persistence)
│   ├── music/                         # Music library
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx                    # Main orchestrator
│   │   ├── hooks/                     # Business logic (Gemini, lights, music)
│   │   ├── components/                # UI components
│   │   ├── lib/                       # Utilities (audio, base64, API client)
│   │   ├── types/                     # TypeScript interfaces
│   │   ├── constants/                 # Configuration constants
│   │   └── worklets/                  # AudioWorklet processors
│   ├── nginx.conf
│   ├── Dockerfile
│   └── package.json
├── raspberry-pi/
│   ├── src/
│   │   ├── iot_client.py              # Main IoT client orchestrator
│   │   ├── gpio_devices.py            # GPIO controller (LED, Buzzer, Motor, Servo)
│   │   ├── websocket_client.py        # WebSocket client for backend
│   │   ├── camera_service.py          # Camera capture service
│   │   └── audio_handler.py           # Audio input/output handler
│   └── scripts/
│       ├── test-dc-motor.py           # Motor testing script
│       ├── test-buzzer.py             # Buzzer testing script
│       └── test-hardware.py           # General hardware test
├── android-app/                       # Kotlin Android app
├── docker-compose.yml
├── start.sh                           # Local dev startup script
├── requirements.txt                   # Root Python deps
├── ITEMS.md                           # Hardware shopping list
└── CLAUDE.md                          # This file
```

## Important Notes

- **Vietnamese-First**: All user-facing text, logs, tool descriptions, system instructions must be in Vietnamese
- **Session Persistence**: Critical for cost optimization - always persist Gemini session on `turn_complete`
- **Thread Safety**: Services use `threading.Lock` for observer lists (accessed from sync/async contexts)
- **Audio Sample Rates**: Input 16kHz (Gemini), Output 24kHz (playback)
- **Camera Permissions**: Always check browser permission states before streaming
- **Fire Alert Caching**: TTS audio generated once and cached in `data/fire_alert_audio.b64`
- **Music Fuzzy Matching**: Tune `MUSIC_SIMILARITY_THRESHOLD` if songs not matching
- **Autoplay Restrictions**: Frontend uses mute fallback + user interaction unlock for music
- **WebSocket Reconnection**: Both Gemini and smart home sockets auto-reconnect (3s delay)

## Testing & Debugging

**Backend Logs**:
```bash
# Watch logs in Docker
docker-compose logs -f backend

# Local development logs are printed to stdout
```

**Frontend Browser Console**:
- Check WebSocket connection status
- Monitor audio pipeline errors
- Verify camera stream permissions

**Common Issues**:
- **No audio playback**: Check browser autoplay policy, ensure user interaction
- **Fire detection not working**: Verify camera permissions, check HSV parameters
- **Gemini not responding**: Verify `GOOGLE_API_KEY`, check session persistence
- **Lights not syncing**: Check WebSocket connection, verify light state JSON
- **Motor not responding**: Ensure IoT client has updated files, check L298N wiring
- **New Gemini tools not working**: Clear `backend/data/session_handle.json` to reset session

## Related Documentation

- Backend details: `backend/CLAUDE.md`
- Frontend details: `frontend/CLAUDE.md`
- Hardware guide: `ITEMS.md` (Vietnamese)
- Motor setup: `raspberry-pi/DC_MOTOR_SETUP.md`
- Motor wiring checklist: `raspberry-pi/MOTOR_WIRING_CHECKLIST.md`
