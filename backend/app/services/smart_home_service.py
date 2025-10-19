import asyncio
import json
import logging
import threading
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple, Literal

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LightState:
    location: str
    is_on: bool = False


class LightingService:
    """Manage the state of smart home lights."""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self.storage_path = storage_path or settings.light_state_file
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._states: Dict[str, LightState] = {}
        self._listeners: List[Tuple[asyncio.AbstractEventLoop, "asyncio.Queue[dict]"]] = []
        self._listener_lock = threading.Lock()
        self._load()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _default_states(self) -> Dict[str, LightState]:
        defaults: Dict[str, LightState] = {}
        for name, is_on in settings.default_lights:
            location_key = name.lower().strip()
            defaults[location_key] = LightState(location=name, is_on=is_on)
        return defaults

    def _load(self) -> None:
        if not self.storage_path.exists():
            self._states = self._default_states()
            self._persist()
            return
        try:
            with self.storage_path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except json.JSONDecodeError:
            logger.warning("Corrupted light state file, recreating it with defaults")
            self._states = self._default_states()
            self._persist()
            return

        states: Dict[str, LightState] = {}
        if isinstance(payload, dict):
            for location_key, raw_state in payload.items():
                if isinstance(raw_state, dict):
                    name = raw_state.get("name", location_key)
                    is_on = bool(raw_state.get("is_on"))
                else:
                    name = str(raw_state)
                    is_on = bool(raw_state)
                normalized_key = location_key.lower().strip()
                states[normalized_key] = LightState(location=name, is_on=is_on)
        else:
            logger.warning("Unexpected light state format; recreating defaults")

        if not states:
            states = self._default_states()
            self._persist()
        else:
            # ensure stable ordering by the display name
            sorted_items = sorted(states.items(), key=lambda item: item[1].location.lower())
            self._states = dict(sorted_items)
            return

        self._states = states

    def _persist(self) -> None:
        with self.storage_path.open("w", encoding="utf-8") as file:
            json.dump(
                {
                    loc: {"name": state.location, "is_on": state.is_on}
                    for loc, state in self._states.items()
                },
                file,
                ensure_ascii=False,
                indent=2,
            )

    # ------------------------------------------------------------------
    # Observer helpers
    # ------------------------------------------------------------------

    def _notify_listeners(self, payload: dict) -> None:
        with self._listener_lock:
            listeners = list(self._listeners)
        for loop, queue in listeners:
            try:
                loop.call_soon_threadsafe(queue.put_nowait, payload)
            except RuntimeError:
                # event loop might be closed; drop the subscriber
                self.remove_listener(queue)

    async def add_listener(self) -> "asyncio.Queue[dict]":
        loop = asyncio.get_running_loop()
        queue: "asyncio.Queue[dict]" = asyncio.Queue()
        with self._listener_lock:
            self._listeners.append((loop, queue))
        # Provide an immediate snapshot to new listeners
        snapshot = [
            {"location": state.location, "is_on": state.is_on}
            for state in self.get_all_states()
        ]
        await queue.put({"type": "snapshot", "lights": snapshot})
        return queue

    def remove_listener(self, queue: "asyncio.Queue[dict]") -> None:
        with self._listener_lock:
            self._listeners = [
                (loop, q)
                for loop, q in self._listeners
                if q is not queue
            ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def toggle_light(self, location: str, turn_on: bool) -> LightState:
        self._load()
        location_key = location.lower().strip()
        display_name = location.strip()
        state = self._states.get(location_key, LightState(location=display_name))
        state.location = display_name
        state.is_on = turn_on
        self._states[location_key] = state
        self._persist()
        logger.info("Light %s is now %s", location_key, "on" if state.is_on else "off")
        self._notify_listeners({"type": "update", "light": asdict(state)})
        return state

    def get_light_state(self, location: str) -> LightState:
        self._load()
        location_key = location.lower().strip()
        state = self._states.get(location_key)
        if state:
            return state
        return LightState(location=location.strip())

    def get_all_states(self) -> Iterable[LightState]:
        self._load()
        return list(self._states.values())


class MusicService:
    """Select a song that best matches the requested title."""

    def __init__(self, music_directory: Optional[Path] = None, threshold: Optional[float] = None) -> None:
        self.music_directory = music_directory or settings.music_directory
        self.threshold = threshold if threshold is not None else settings.music_similarity_threshold
        self.music_directory.mkdir(parents=True, exist_ok=True)
        self._catalog = self._build_catalog()

    def _build_catalog(self) -> List[str]:
        supported_ext = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"}
        catalog = []
        if not self.music_directory.exists():
            return catalog
        for item in self.music_directory.iterdir():
            if item.is_file() and item.suffix.lower() in supported_ext:
                catalog.append(item.stem)
        return catalog

    def refresh(self) -> None:
        self._catalog = self._build_catalog()

    def list_available_songs(self) -> List[str]:
        if not self._catalog:
            self.refresh()
        return list(self._catalog)

    def _similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(a=a.lower(), b=b.lower()).ratio()

    def choose_song(self, requested_title: str) -> Optional[str]:
        if not requested_title:
            return None
        if not self._catalog:
            self.refresh()
        if not self._catalog:
            return None
        best_match = max(
            self._catalog,
            key=lambda track: self._similarity(requested_title, track),
        )
        score = self._similarity(requested_title, best_match)
        logger.info("Best song match for '%s' is '%s' (score %.3f)", requested_title, best_match, score)
        if score >= self.threshold:
            return best_match
        return None

    def find_song_file(self, track_title: str) -> Optional[Path]:
        if not track_title:
            return None
        if not self.music_directory.exists():
            return None
        for item in self.music_directory.iterdir():
            if item.is_file() and item.stem == track_title:
                return item
        return None


@dataclass
class MusicPlaybackState:
    requested_title: Optional[str] = None
    matched_song: Optional[str] = None
    status: Literal["stopped", "playing", "paused"] = "stopped"

    def copy(self) -> "MusicPlaybackState":
        return MusicPlaybackState(
            requested_title=self.requested_title,
            matched_song=self.matched_song,
            status=self.status,
        )


class SmartHomeService:
    def __init__(
        self,
        lighting_service: Optional[LightingService] = None,
        music_service: Optional[MusicService] = None,
    ) -> None:
        self.lighting_service = lighting_service or LightingService()
        self.music_service = music_service or MusicService()
        self._music_playback_state = MusicPlaybackState()

    def turn_on_light(self, location: str) -> LightState:
        return self.lighting_service.toggle_light(location, True)

    def turn_off_light(self, location: str) -> LightState:
        return self.lighting_service.toggle_light(location, False)

    def play_music(self, title: str) -> Optional[str]:
        matched = self.music_service.choose_song(title)
        if matched:
            self._music_playback_state = MusicPlaybackState(
                requested_title=title,
                matched_song=matched,
                status="playing",
            )
        else:
            self._music_playback_state = MusicPlaybackState(
                requested_title=title,
                matched_song=None,
                status="stopped",
            )
        return matched

    def get_song_file(self, title: str) -> Optional[Path]:
        return self.music_service.find_song_file(title)

    def get_lights(self) -> List[LightState]:
        return list(self.lighting_service.get_all_states())

    def list_music(self) -> List[str]:
        return self.music_service.list_available_songs()

    def get_music_playback_state(self) -> MusicPlaybackState:
        return self._music_playback_state.copy()

    def pause_music(self) -> Optional[str]:
        if self._music_playback_state.matched_song and self._music_playback_state.status == "playing":
            self._music_playback_state.status = "paused"
            return self._music_playback_state.matched_song
        return None

    def continue_music(self) -> Optional[str]:
        if self._music_playback_state.matched_song and self._music_playback_state.status == "paused":
            self._music_playback_state.status = "playing"
            return self._music_playback_state.matched_song
        return None


_global_smart_home_service: Optional[SmartHomeService] = None


def get_smart_home_service() -> SmartHomeService:
    global _global_smart_home_service
    if _global_smart_home_service is None:
        _global_smart_home_service = SmartHomeService()
    return _global_smart_home_service
