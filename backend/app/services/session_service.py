import json
from pathlib import Path
from typing import Optional

from app.core.config import settings


class SessionService:
    """Service to persist the Gemini session handle locally."""

    def __init__(self, storage_file: Optional[Path] = None) -> None:
        self.storage_file = storage_file or settings.session_handle_file
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)

    def save_previous_session_handle(self, handle: str) -> None:
        payload = {"session_handle": handle}
        with self.storage_file.open("w", encoding="utf-8") as file:
            json.dump(payload, file)

    def load_previous_session_handle(self) -> Optional[str]:
        if not self.storage_file.exists():
            return None
        try:
            with self.storage_file.open("r", encoding="utf-8") as file:
                payload = json.load(file)
            return payload.get("session_handle")
        except json.JSONDecodeError:
            return None
