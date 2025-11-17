"""
Configuration loader cho IoT Client
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


def get_env_str(key: str, default: str) -> str:
    """Get string environment variable"""
    return os.getenv(key, default)


def get_env_int(key: str, default: int) -> int:
    """Get integer environment variable"""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def get_env_float(key: str, default: float) -> float:
    """Get float environment variable"""
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default


def get_env_bool(key: str, default: bool) -> bool:
    """Get boolean environment variable"""
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


@dataclass
class GPIOPinConfig:
    """GPIO pin configuration"""
    living_room: int = 17
    bedroom: int = 27
    kitchen: int = 22
    balcony: int = 23
    bathroom: int = 24

    @classmethod
    def from_env(cls) -> "GPIOPinConfig":
        """Load từ environment variables"""
        return cls(
            living_room=get_env_int("GPIO_LIVING_ROOM", 17),
            bedroom=get_env_int("GPIO_BEDROOM", 27),
            kitchen=get_env_int("GPIO_KITCHEN", 22),
            balcony=get_env_int("GPIO_BALCONY", 23),
            bathroom=get_env_int("GPIO_BATHROOM", 24),
        )


@dataclass
class CameraSettings:
    """Camera configuration"""
    device_index: int = 0
    width: int = 1280
    height: int = 720
    fps: int = 30
    capture_interval: float = 0.5
    jpeg_quality: int = 75
    max_dimension: int = 720

    @classmethod
    def from_env(cls) -> "CameraSettings":
        """Load từ environment variables"""
        return cls(
            device_index=get_env_int("CAMERA_DEVICE_INDEX", 0),
            width=get_env_int("CAMERA_WIDTH", 1280),
            height=get_env_int("CAMERA_HEIGHT", 720),
            fps=get_env_int("CAMERA_FPS", 30),
            capture_interval=get_env_float("CAMERA_CAPTURE_INTERVAL", 0.5),
            jpeg_quality=get_env_int("CAMERA_JPEG_QUALITY", 75),
            max_dimension=get_env_int("CAMERA_MAX_DIMENSION", 720),
        )


@dataclass
class AudioSettings:
    """Audio configuration"""
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1600

    @classmethod
    def from_env(cls) -> "AudioSettings":
        """Load từ environment variables"""
        return cls(
            sample_rate=get_env_int("AUDIO_SAMPLE_RATE", 16000),
            channels=get_env_int("AUDIO_CHANNELS", 1),
            chunk_size=get_env_int("AUDIO_CHUNK_SIZE", 1600),
        )


@dataclass
class WebSocketSettings:
    """WebSocket configuration"""
    server_url: str = "ws://localhost:8000/ws/gemini"
    reconnect_delay: float = 3.0
    ping_interval: float = 10.0
    ping_timeout: float = 30.0

    @classmethod
    def from_env(cls) -> "WebSocketSettings":
        """Load từ environment variables"""
        return cls(
            server_url=get_env_str("BACKEND_URL", "ws://localhost:8000/ws/gemini"),
            reconnect_delay=get_env_float("WS_RECONNECT_DELAY", 3.0),
            ping_interval=get_env_float("WS_PING_INTERVAL", 10.0),
            ping_timeout=get_env_float("WS_PING_TIMEOUT", 30.0),
        )


@dataclass
class AppConfig:
    """Main application configuration"""
    mock_mode: bool = False
    log_level: str = "INFO"
    log_file: str = "/var/log/iot-client.log"

    gpio_pins: GPIOPinConfig = None
    camera: CameraSettings = None
    audio: AudioSettings = None
    websocket: WebSocketSettings = None

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load toàn bộ config từ environment"""
        return cls(
            mock_mode=get_env_bool("MOCK_MODE", False),
            log_level=get_env_str("LOG_LEVEL", "INFO"),
            log_file=get_env_str("LOG_FILE", "/var/log/iot-client.log"),
            gpio_pins=GPIOPinConfig.from_env(),
            camera=CameraSettings.from_env(),
            audio=AudioSettings.from_env(),
            websocket=WebSocketSettings.from_env(),
        )


# Global config instance
config = AppConfig.from_env()
