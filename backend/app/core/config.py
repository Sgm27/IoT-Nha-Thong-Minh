from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional


def _env_path(name: str, default: Path) -> Path:
    value = os.getenv(name)
    return Path(value) if value else default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value is not None else default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value is not None else default


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
    default_lights: tuple[tuple[str, bool], ...] = field(
        default_factory=lambda: (
            ("Phòng khách", True),
            ("Phòng ngủ", False),
            ("Nhà bếp", True),
            ("Ban công", False),
            ("Nhà tắm", True),
        )
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
