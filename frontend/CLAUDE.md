# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IoT Smart Home Frontend - A React + TypeScript frontend for controlling smart home devices with voice and camera integration through Google's Gemini Live API. Built with Vite, TailwindCSS, and WebSockets for real-time communication.

**Primary Language**: Vietnamese (all user-facing text is in Vietnamese)

## Development Commands

### Running the Application

**Local Development:**
```bash
# From frontend directory
npm run dev
# Runs on http://localhost:5173 with hot reload
```

**Build for Production:**
```bash
npm run build
# Outputs to dist/ directory
```

**Preview Production Build:**
```bash
npm run preview
```

**Docker (Recommended):**
```bash
# From project root
docker-compose up --build

# Frontend only
docker-compose up frontend
```

### Dependencies

```bash
npm install
```

Key dependencies:
- React 18 + React DOM (UI framework)
- Vite (build tool with SWC for fast compilation)
- TailwindCSS (utility-first CSS)
- TypeScript (type safety)
- shadcn/ui components (via class-variance-authority, clsx, tailwind-merge)

## Architecture

### Core Design Pattern: Custom Hooks + Component Composition

The frontend follows a hooks-based architecture where business logic is encapsulated in custom hooks and UI is composed from reusable components.

**Main Application** (`src/App.tsx`):
- Orchestrates three major features: Lights, Music, and Gemini Chat
- Uses three primary custom hooks that handle all business logic
- Provides shared feedback mechanism to all hooks

**Hook Layer** (`src/hooks/`):
- `useGeminiRealtime.ts` - **Primary orchestrator** for Gemini WebSocket communication
- `useLights.ts` - Light state management and control
- `useMusicController.ts` - Music playback and library management

**Component Layer** (`src/components/`):
- `LightControlCard.tsx` - UI for controlling lights
- `MusicControlCard.tsx` - UI for music player
- `GeminiChatCard.tsx` - Chat interface with voice/camera support
- `ui/` - Reusable shadcn/ui components (Button, Card, Input, etc.)

**Type Definitions** (`src/types/`):
- `smart-home.ts` - Light and music state interfaces
- `chat.ts` - Chat message structures

### Key Architectural Concepts

**1. WebSocket Communication (useGeminiRealtime.ts)**

The `useGeminiRealtime` hook manages the primary WebSocket connection to `/ws/gemini`:

- **Bidirectional Streaming**:
  - **Client → Server**: Text messages, voice (PCM audio), images, camera frames
  - **Server → Client**: Gemini audio responses, text, transcriptions, tool call notifications, smart home updates

- **Three Concurrent Media Streams**:
  - **Text Input**: Standard chat messages
  - **Audio Input**: Real-time microphone capture using Web Audio API + AudioWorklet
  - **Camera Input**: Periodic frame capture for fire detection (configurable interval)

- **Audio Pipeline**:
  - Microphone → AudioContext → AudioWorkletNode (`pcm-worklet-processor.js`)
  - Resampling: Input audio → 16kHz PCM16 (expected by Gemini)
  - Playback: Base64 PCM chunks from Gemini → AudioBuffer → AudioContext playback queue
  - Queue management prevents audio overlap and stuttering

- **Camera Integration**:
  - Video element → Canvas → JPEG compression → Base64
  - Automatic downscaling to 720px max dimension
  - Dynamic capture interval based on server configuration
  - Permission handling for camera access

- **Session Persistence**: WebSocket automatically reconnects on disconnect with 3-second retry

**2. Smart Home State Management**

Two independent subsystems with real-time updates:

**Lights (`useLights.ts`)**:
- WebSocket at `/smart-home/lights/stream` for real-time state updates
- REST endpoints for control actions (`/smart-home/lights/on`, `/smart-home/lights/off`)
- Local state synchronization with snapshot/update messages
- Location-based light identification with normalization

**Music (`useMusicController.ts`)**:
- WebSocket at `/smart-home/music/updates` for state synchronization
- HTML5 Audio element for actual playback
- Two-way sync: Browser controls → Backend API, Backend state → Browser playback
- Autoplay handling with mute fallback for browser restrictions
- Position tracking: Server position + client-side animation frame interpolation

**3. Voice & Camera Integration**

**Voice Input**:
- Uses AudioWorklet for low-latency audio processing
- Worklet loaded from `src/worklets/pcm-worklet-processor.js`
- Handles resampling from browser sample rate → 16kHz
- Chunks audio into 100ms windows for streaming
- Permission denied state tracking

**Camera Streaming**:
- getUserMedia API with ideal resolution 720p
- Canvas-based frame capture and compression
- JPEG quality: 0.75, max size: 4MB
- Sends frames at interval specified by server (default 500ms)
- Automatic cleanup on disconnect

**4. Type-Safe API Communication**

All HTTP requests use the generic `apiClient<T>()` helper:
```typescript
const data = await apiClient<LightState[]>("/smart-home/lights");
```

Benefits:
- Automatic JSON parsing with type inference
- Consistent error handling (extracts `.detail` from FastAPI errors)
- 204 No Content handling

### WebSocket Message Protocol

**Client → Server:**
```json
{"text": "string"}
{"realtime_input": {"media_chunks": [{"mime_type": "audio/pcm;rate=16000", "data": "base64..."}]}}
{"realtime_input": {"media_chunks": [{"mime_type": "image/jpeg", "data": "base64..."}]}}
{"keepalive": {"timestamp": "ISO8601"}}
```

**Server → Client:**
```json
{"setupComplete": {...}}
{"text": "string"}
{"audio": {"data": "base64...", "mime_type": "audio/pcm", "sample_rate": 24000}}
{"transcription": {"text": "...", "sender": "User|Gemini", "finished": bool}}
{"type": "smart_home_light_update", "location": "...", "is_on": bool}
{"type": "smart_home_music", "matched_song": "...", "stream_url": "..."}
{"type": "smart_home_music_control", "action": "pause|continue", "status": "..."}
{"type": "fire_detection_alert", "message": "...", "audio_base64": "..."}
{"type": "keepalive"}
```

## Common Development Patterns

### Adding a New Smart Home Control

1. Add type definitions in `src/types/smart-home.ts`
2. Create custom hook in `src/hooks/useYourFeature.ts`:
   - WebSocket subscription for real-time updates
   - REST API calls for control actions
   - Local state management
3. Create UI component in `src/components/YourFeatureCard.tsx`
4. Import hook and component in `src/App.tsx`
5. Update backend `gemini_service.py` with corresponding tool

### Handling New Gemini Message Types

In `useGeminiRealtime.ts`, add handler in `handleGeminiPayload()`:
```typescript
case "your_new_type": {
  const data = typeof data.field === "string" ? data.field : "";
  appendChatMessage({ role: "system", content: "..." });
  // Perform action
  return;
}
```

### Audio Resampling & Format Conversion

All audio utilities in `src/lib/audio.ts`:
- `resampleFloat32()` - Linear interpolation resampling
- `float32ToPCM16()` - Convert Float32Array → Int16 PCM
- `decodeAudioChunk()` - Base64 → AudioBuffer
- `concatFloat32()` - Join audio chunks

### Working with Images

Image utilities in `src/lib/base64.ts`:
- `arrayBufferToBase64()` - Binary → Base64 string
- `base64ToArrayBuffer()` - Base64 → ArrayBuffer

Maximum image size: 4MB (`MAX_IMAGE_SIZE_BYTES` in `src/constants/gemini.ts`)

## Docker & Production Deployment

**Multi-stage Dockerfile**:
1. Build stage: Node 20 Alpine → npm ci → npm run build
2. Production stage: nginx:1.25-alpine serves static files

**Nginx Configuration** (`nginx.conf`):
- Serves built React app from `/usr/share/nginx/html`
- Proxies API requests to backend:
  - `/smart-home/*` → `http://backend:8000/smart-home/*`
  - `/ws/*` → `http://backend:8000/ws/*` (WebSocket upgrade support)
  - `/assistant/*` → `http://backend:8000/assistant/*`
- SPA fallback: All routes serve `index.html`

**Environment Variables**:
- `VITE_BACKEND_URL` - Backend URL for dev proxy (default: `http://localhost:8000`)
- Set in `.env` for local development, overridden by Docker Compose

## Path Aliases

Configured in `vite.config.ts` and `tsconfig.json`:
```typescript
import { Component } from "@/components/Component"
```

`@/` resolves to `src/`

## Styling Conventions

**TailwindCSS Utility-First**:
- Component variants managed via `class-variance-authority`
- Conditional classes via `clsx` and `tailwind-merge` (exported as `cn()` from `@/lib/utils`)
- Theme uses CSS variables defined in `src/index.css`
- Custom animations in `tailwind.config.ts` via `tailwindcss-animate`

**Example Pattern**:
```tsx
<div className={cn(
  "base-classes",
  condition && "conditional-classes"
)}>
```

## Important Notes

- **Vietnamese-First**: All user-facing text must be in Vietnamese
- **Audio Sample Rates**: Input 16kHz (Gemini), Output 24kHz (playback)
- **WebSocket Reconnection**: Both Gemini and smart home sockets auto-reconnect with 3s delay
- **Autoplay Restrictions**: Music playback uses mute fallback + user interaction unlock
- **Camera Permissions**: Always check `isCameraStreaming` and `cameraError` states
- **Microphone Permissions**: Track `isMicPermissionDenied` for UX feedback
- **AudioWorklet Loading**: Must use `new URL(..., import.meta.url)` for Vite compatibility
- **Message Streaming**: Assistant messages stream incrementally via `streaming: true` flag
- **Fire Detection**: Camera frames sent to backend for OpenCV-based fire detection

## Integration with Backend

Backend runs on port 8000 (FastAPI). See `../backend/CLAUDE.md` for:
- REST API endpoints (`/smart-home/lights`, `/smart-home/music`, etc.)
- WebSocket protocols and message formats
- Gemini Live configuration and tool definitions
- Fire detection parameters

Frontend expects these backend endpoints to be available either:
- Via Vite dev proxy (configured in `vite.config.ts`)
- Via Nginx reverse proxy (production Docker setup)
