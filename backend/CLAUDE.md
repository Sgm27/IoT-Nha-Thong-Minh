# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IoT Smart Home Backend - A FastAPI-based backend system for an IoT smart home application that integrates with Google's Gemini Live API for voice-controlled home automation. The system manages lights, music playback, and fire detection using camera feeds.

**Primary Language**: Vietnamese (all user-facing messages, tool descriptions, and system instructions are in Vietnamese)

## Development Commands

### Running the Application

**Local Development:**
```bash
# From backend directory
uvicorn app.main:create_app --host 0.0.0.0 --port 8000 --reload
```

**Docker (Recommended):**
```bash
# From project root
docker-compose up --build

# Backend only
docker-compose up backend
```

### Environment Setup

1. Copy `.env.example` to `.env` in the backend directory
2. Set required environment variables:
   - `GOOGLE_API_KEY`: Required for Gemini Live integration
   - `GEMINI_MODEL`: Default is "gemini-live-2.5-flash-preview"
   - Configure file paths if non-default locations are needed

### Dependencies

Install from project root:
```bash
pip install -r requirements.txt
```

Key dependencies:
- FastAPI + Uvicorn (web framework)
- google-genai (Gemini Live API)
- opencv-python + numpy (fire detection)
- mutagen (music metadata)
- python-dotenv (configuration)

## Architecture

### Core Design Pattern: Service-Oriented Architecture

The backend follows a layered architecture with clear separation of concerns:

**API Layer** (`app/api/routes/`):
- `websocket.py` - Main Gemini Live WebSocket endpoint at `/ws/gemini`
- `smart_home.py` - REST endpoints for lights and music control under `/smart-home`
- `assistant.py` - Additional assistant endpoints

**Service Layer** (`app/services/`):
- `gemini_service.py` - **Primary orchestrator** for Gemini Live WebSocket connections
- `smart_home_service.py` - Manages `LightingService` and `MusicService`
- `fire_detection_service.py` - Wraps OpenCV fire detector with throttling
- `session_service.py` - Persists resumable Gemini session handles
- `notification_voice_service.py` - Generates voice notifications

**Configuration** (`app/core/config.py`):
- Single source of truth using dataclass `Settings` with environment variable helpers
- All settings accessed via `settings` singleton

### Key Architectural Concepts

**1. Gemini Live Integration (gemini_service.py)**

The `GeminiService` class orchestrates bidirectional streaming between the client and Gemini:

- **Three concurrent tasks**:
  - `_relay_client_to_gemini()` - forwards client messages (text, audio, images) to Gemini
  - `_relay_gemini_to_client()` - streams Gemini responses (audio, transcriptions, tool calls) to client
  - `_ping_websocket()` - keeps WebSocket alive

- **Session Resumption**: Uses `SessionService` to persist and restore Gemini session handles, maintaining conversation context across reconnections

- **Function Calling**: Gemini can invoke smart home tools (turn_on_light, turn_off_light, play_music, pause_music, continue_music) defined in `_create_live_config()`

- **Realtime Input Processing**: Handles both audio chunks (for voice) and image frames (for camera/fire detection) via `realtime_input` messages

**2. Smart Home State Management (smart_home_service.py)**

Two independent services managed by `SmartHomeService`:

- **LightingService**:
  - Persists light states to JSON file (`data/light_state.json`)
  - Supports observer pattern via `add_listener()` for real-time WebSocket updates
  - Default lights configured in `settings.default_lights`

- **MusicService**:
  - Uses fuzzy string matching (`SequenceMatcher`) to find songs in `music/` directory
  - Threshold configurable via `MUSIC_SIMILARITY_THRESHOLD` (default 0.72)
  - `MusicPlaybackState` tracks current song, status (playing/paused/stopped), and position

Both services use thread-safe observer pattern to notify WebSocket clients of state changes.

**3. Fire Detection Pipeline (fire_detection_service.py)**

- Receives image frames from client via Gemini WebSocket
- `FireDetector` (in `app/utils/fire_detection.py`) uses OpenCV to detect fire regions
- Alert cooldown mechanism prevents spam (configurable via `FIRE_ALERT_COOLDOWN_SECONDS`)
- Voice notification audio cached in `data/fire_alert_audio.b64`
- Detection payload includes confidence, fire percentage, and region count

**4. Data Persistence Strategy**

All stateful data stored in `data/` directory:
- `conversation_history.json` - Full chat history with timestamps
- `session_handle.json` - Resumable Gemini session + token usage
- `light_state.json` - Current state of all lights
- `images/` - Optional captured camera frames (if `SAVE_CAPTURED_IMAGE=True`)

JSON files reloaded on each operation to support concurrent access patterns.

### WebSocket Message Protocol

**Client → Server:**
```json
{"text": "string"}  // Text message
{"realtime_input": {"media_chunks": [{"mime_type": "audio/pcm", "data": "base64..."}]}}
{"voice_notification_request": {"text": "...", "request_id": "..."}}
{"keepalive": true}
```

**Server → Client:**
```json
{"audio": "base64..."}  // Gemini audio response
{"text": "string"}  // Text response
{"transcription": {"text": "...", "sender": "User|Gemini", "finished": bool}}
{"type": "smart_home_light_update", "location": "...", "is_on": bool}
{"type": "smart_home_music", "matched_song": "...", "stream_url": "..."}
{"type": "fire_detection_alert", "message": "...", "audio_base64": "..."}
```

## Common Development Patterns

### Adding a New Smart Home Device Type

1. Add state management service in `smart_home_service.py` (similar to `LightingService`)
2. Add tool declaration in `GeminiService._create_live_config()` tools array
3. Add tool handler in `GeminiService._handle_tool_calls()`
4. Create REST endpoints in `smart_home.py` for direct HTTP access
5. Update system instruction in `GeminiService.SYSTEM_INSTRUCTION` (in Vietnamese)

### Modifying Gemini Configuration

Key parameters in `_create_live_config()`:
- `voice_name`: Voice for TTS (currently "Aoede")
- `language_code`: "vi-VN" for Vietnamese
- `temperature`: 0.6 (creativity level)
- `top_p`: 0.85 (nucleus sampling)

### Working with Fire Detection

Fire detection logic in `app/utils/fire_detection.py` uses OpenCV color space filtering. Adjust `FireParams` for sensitivity:
- HSV color range for flame detection
- Minimum contour area to filter noise
- Threshold for fire percentage in frame

## Testing Considerations

**Offline Mode**: When `GOOGLE_API_KEY` is missing, `GeminiService` enters offline echo mode via `_run_offline_loop()` - useful for testing WebSocket infrastructure without Gemini.

**Tool Testing**: Tools can be tested via `{"tool_call": {...}}` messages in offline mode.

## File Organization

```
backend/
├── app/
│   ├── main.py              # FastAPI app factory
│   ├── core/
│   │   ├── config.py        # Environment-based configuration
│   │   └── logging_config.py
│   ├── api/routes/          # HTTP & WebSocket endpoints
│   ├── services/            # Business logic layer
│   ├── utils/               # Pure utility functions (fire detection)
│   └── scripts/             # One-off scripts (e.g., audio generation)
├── data/                    # Runtime state persistence
├── music/                   # Music library (MP3/WAV/FLAC/etc)
├── Dockerfile
└── .env.example
```

## Important Notes

- **Vietnamese-First**: All user-facing text (logs, responses, tool descriptions) should be in Vietnamese
- **Session Handle Persistence**: Critical for token cost optimization - always persist on `turn_complete`
- **Thread Safety**: Services use `threading.Lock` for observer lists since they're accessed from both sync (persistence) and async (WebSocket) contexts
- **Fire Alert Audio**: Generated once and cached to avoid repeated TTS calls
- **Music Similarity**: Tune `MUSIC_SIMILARITY_THRESHOLD` if songs aren't matching properly
- **Capture Interval**: `CAPTURE_INTERVAL_SECONDS` controls camera frame rate - balance between responsiveness and CPU usage

## Hardware Integration Context

This backend is designed to run on Raspberry Pi with:
- Camera (CSI module or USB webcam) for fire detection
- USB microphone for voice input
- Speaker for audio output
- 4-channel relay module for light control (connected via GPIO)
- LED lights or real AC devices connected through relays

See `ITEMS.md` in project root for complete hardware shopping list and wiring guide.
