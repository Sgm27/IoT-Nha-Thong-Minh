import json
import datetime as dt
from pathlib import Path
from typing import Dict, Optional

from app.core.config import settings


class SessionService:
    """Service to persist the Gemini session handle locally."""

    def __init__(self, storage_file: Optional[Path] = None) -> None:
        self.storage_file = storage_file or settings.session_handle_file
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self.timeout_seconds = settings.session_timeout_seconds
        self._last_token_usage: Optional[Dict[str, int]] = None

    def save_previous_session_handle(
        self, handle: str, *, token_usage: Optional[Dict[str, int]] = None
    ) -> None:
        payload: Dict[str, object] = {
            "session_handle": handle,
            "saved_at": dt.datetime.utcnow().isoformat(),
        }
        usage_to_store = token_usage if token_usage is not None else self._last_token_usage
        if usage_to_store:
            payload["token_usage"] = dict(usage_to_store)
            self._last_token_usage = dict(usage_to_store)
        else:
            self._last_token_usage = None
        with self.storage_file.open("w", encoding="utf-8") as file:
            json.dump(payload, file)

    def load_previous_session_handle(self) -> Optional[str]:
        if not self.storage_file.exists():
            return None
        try:
            with self.storage_file.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except (json.JSONDecodeError, OSError):
            return None
        handle = payload.get("session_handle")
        saved_at_raw = payload.get("saved_at")
        token_usage = payload.get("token_usage")

        if not handle or not saved_at_raw:
            self._last_token_usage = None
            return None

        try:
            saved_at = dt.datetime.fromisoformat(saved_at_raw)
        except (TypeError, ValueError):
            self._last_token_usage = None
            return None

        elapsed = (dt.datetime.utcnow() - saved_at).total_seconds()
        if elapsed <= self.timeout_seconds:
            if isinstance(token_usage, dict):
                # Filter out non-numeric entries to keep storage clean
                filtered_usage: Dict[str, int] = {
                    key: int(value)
                    for key, value in token_usage.items()
                    if isinstance(value, (int, float))
                }
                self._last_token_usage = filtered_usage or None
            else:
                self._last_token_usage = None
            return handle

        self._last_token_usage = None
        return None

    def get_last_token_usage(self) -> Optional[Dict[str, int]]:
        return self._last_token_usage.copy() if self._last_token_usage else None
