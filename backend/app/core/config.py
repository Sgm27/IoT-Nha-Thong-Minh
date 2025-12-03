from __future__ import annotations

import os

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


load_dotenv()


def _env_path(name: str, default: Path) -> Path:
    value = os.getenv(name)
    return Path(value) if value else default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value is not None else default


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    return default


def _env_str(name: str, default: Optional[str]) -> Optional[str]:
    value = os.getenv(name)
    if value is None:
        return default
    return value


@dataclass
class Settings:
    app_name: str = field(default_factory=lambda: _env_str("APP_NAME", "IoT Smart Home"))
    google_api_key: Optional[str] = field(
        default_factory=lambda: _env_str("GOOGLE_API_KEY", None)
    )
    gemini_model: str = field(
        default_factory=lambda: _env_str("GEMINI_MODEL", "gemini-live-2.5-flash-preview")
    )
    conversation_history_file: Path = field(
        default_factory=lambda: _env_path(
            "CONVERSATION_HISTORY_FILE", Path("data") / "conversation_history.json"
        )
    )
    session_handle_file: Path = field(
        default_factory=lambda: _env_path(
            "SESSION_HANDLE_FILE", Path("data") / "session_handle.json"
        )
    )
    session_timeout_seconds: int = field(
        default_factory=lambda: _env_int("SESSION_TIMEOUT_SECONDS", 300)
    )
    light_state_file: Path = field(
        default_factory=lambda: _env_path("LIGHT_STATE_FILE", Path("data") / "light_state.json")
    )
    music_directory: Path = field(
        default_factory=lambda: _env_path("MUSIC_DIRECTORY", Path("music"))
    )
    music_similarity_threshold: float = field(
        default_factory=lambda: _env_float("MUSIC_SIMILARITY_THRESHOLD", 0.72)
    )
    websocket_ping_interval: int = field(
        default_factory=lambda: _env_int("WEBSOCKET_PING_INTERVAL", 10)
    )
    websocket_receive_timeout: int = field(
        default_factory=lambda: _env_int("WEBSOCKET_RECEIVE_TIMEOUT", 30)
    )
    websocket_config_timeout: int = field(
        default_factory=lambda: _env_int("WEBSOCKET_CONFIG_TIMEOUT", 10)
    )
    save_captured_image: bool = field(
        default_factory=lambda: _env_bool("SAVE_CAPTURED_IMAGE", False)
    )
    captured_images_directory: Path = field(
        default_factory=lambda: _env_path("CAPTURED_IMAGES_DIRECTORY", Path("data") / "images")
    )
    capture_interval_seconds: float = field(
        default_factory=lambda: max(0.1, _env_float("CAPTURE_INTERVAL_SECONDS", 0.5))
    )
    fire_alert_cooldown_seconds: float = field(
        default_factory=lambda: max(0.0, _env_float("FIRE_ALERT_COOLDOWN_SECONDS", 10.0))
    )
    fire_alert_audio_file: Path = field(
        default_factory=lambda: _env_path(
            "FIRE_ALERT_AUDIO_FILE", Path("data") / "fire_alert_audio.b64"
        )
    )
    default_lights: tuple[tuple[str, bool], ...] = field(
        default_factory=lambda: (
            ("Phòng khách", False),
            ("Phòng ngủ", False),
            ("Bếp", False),
        )
    )
    # Face++ Recognition Settings
    facepp_api_key: Optional[str] = field(
        default_factory=lambda: _env_str("FACEPP_API_KEY", None)
    )
    facepp_api_secret: Optional[str] = field(
        default_factory=lambda: _env_str("FACEPP_API_SECRET", None)
    )
    facepp_compare_url: str = field(
        default_factory=lambda: _env_str(
            "FACEPP_COMPARE_URL", "https://api-us.faceplusplus.com/facepp/v3/compare"
        )
    )
    host_faces_directory: Path = field(
        default_factory=lambda: _env_path("HOST_FACES_DIRECTORY", Path("data") / "host")
    )
    face_recognition_threshold: float = field(
        default_factory=lambda: _env_float("FACE_RECOGNITION_THRESHOLD", 80.0)
    )
    face_recognition_enabled: bool = field(
        default_factory=lambda: _env_bool("FACE_RECOGNITION_ENABLED", True)
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
