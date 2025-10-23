"""Service responsible for processing camera frames and emitting fire alerts."""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.services.notification_voice_service import NotificationVoiceService
from app.utils.fire_detection import FireDetector, FireParams

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class FireAlertPayload:
    """Serializable payload sent to the mobile client when a fire is detected."""

    message: str
    detection: dict
    audio_base64: Optional[str]
    audio_format: str
    audio_sample_rate: Optional[int]
    triggered_at: str
    source_mime_type: Optional[str]

    def to_dict(self) -> dict:
        payload = {
            "type": "fire_detection_alert",
            "message": self.message,
            "detection": self.detection,
            "triggered_at": self.triggered_at,
            "source_mime_type": self.source_mime_type,
        }
        if self.audio_base64:
            payload.update(
                {
                    "audio_base64": self.audio_base64,
                    "audio_format": self.audio_format,
                }
            )
            if self.audio_sample_rate:
                payload["audio_sample_rate"] = self.audio_sample_rate
        return payload


class FireDetectionService:
    """Wraps the OpenCV based detector with throttling and alert generation."""

    ALERT_MESSAGE_TEMPLATE = (
        "🚨 Cảnh báo cháy! Phát hiện {regions} vùng lửa với độ tin cậy {confidence}% "
        "(chiếm {percentage}% khung hình). Vui lòng kiểm tra ngay!"
    )

    def __init__(
        self,
        detector: Optional[FireDetector] = None,
        notification_voice_service: Optional[NotificationVoiceService] = None,
        cooldown_seconds: Optional[float] = None,
        alert_audio_path: Optional[Path] = None,
    ) -> None:
        self.detector = detector or FireDetector(FireParams())
        self.notification_voice_service = (
            notification_voice_service or NotificationVoiceService()
        )
        self.cooldown_seconds = (
            settings.fire_alert_cooldown_seconds
            if cooldown_seconds is None
            else max(0.0, cooldown_seconds)
        )
        self.alert_audio_path = (
            settings.fire_alert_audio_file if alert_audio_path is None else alert_audio_path
        )
        self.alert_audio_path.parent.mkdir(parents=True, exist_ok=True)

        self._last_alert_monotonic: Optional[float] = None
        self._alert_audio_base64: Optional[str] = None
        self._alert_audio_lock = asyncio.Lock()

    async def process_image(self, data: bytes, mime_type: Optional[str]) -> Optional[dict]:
        """Analyse an image and optionally return an alert payload."""

        detection = await self.detector.detect_from_bytes_async(data)
        has_fire = bool(detection.get("has_fire"))
        if not has_fire:
            logger.debug(
                "🔥 Không phát hiện lửa (confidence=%s%%)", detection.get("confidence", 0.0)
            )
            return None

        if not self._should_emit_alert():
            logger.debug("🔥 Đã phát hiện lửa nhưng đang trong thời gian chờ cảnh báo tiếp theo")
            return None

        self._last_alert_monotonic = time.monotonic()
        audio_base64 = await self._get_or_generate_alert_audio()

        payload = FireAlertPayload(
            message=self._build_message(detection),
            detection=detection,
            audio_base64=audio_base64,
            audio_format="audio/pcm",
            audio_sample_rate=self.notification_voice_service.SAMPLE_RATE,
            triggered_at=dt.datetime.utcnow().isoformat(),
            source_mime_type=mime_type,
        )
        logger.warning(
            "🚨 FIRE DETECTED: confidence=%s%% regions=%s percentage=%s%%",
            detection.get("confidence"),
            detection.get("fire_regions"),
            detection.get("fire_percentage"),
        )
        return payload.to_dict()

    def _should_emit_alert(self) -> bool:
        if self.cooldown_seconds <= 0:
            return True
        if self._last_alert_monotonic is None:
            return True
        return (time.monotonic() - self._last_alert_monotonic) >= self.cooldown_seconds

    def _build_message(self, detection: dict) -> str:
        try:
            confidence = float(detection.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
        try:
            percentage = float(detection.get("fire_percentage", 0.0))
        except (TypeError, ValueError):
            percentage = 0.0
        try:
            regions = int(detection.get("fire_regions", 0))
        except (TypeError, ValueError):
            regions = 0

        return self.ALERT_MESSAGE_TEMPLATE.format(
            confidence=round(confidence, 2),
            percentage=round(percentage, 2),
            regions=max(regions, 1),
        )

    async def _get_or_generate_alert_audio(self) -> Optional[str]:
        async with self._alert_audio_lock:
            if self._alert_audio_base64:
                return self._alert_audio_base64

            if self.alert_audio_path.exists():
                try:
                    content = self.alert_audio_path.read_text(encoding="utf-8").strip()
                    if content:
                        self._alert_audio_base64 = content
                        logger.debug("🔊 Đã tải âm thanh cảnh báo cháy từ %s", self.alert_audio_path)
                        return self._alert_audio_base64
                except OSError:
                    logger.exception(
                        "❌ Không thể đọc file âm thanh cảnh báo tại %s", self.alert_audio_path
                    )

            try:
                base64_audio = await self.notification_voice_service.generate_voice_notification_base64(
                    "Cảnh báo cháy! Vui lòng kiểm tra khu vực ngay lập tức."
                )
            except Exception:  # pylint: disable=broad-except
                logger.exception("❌ Không thể tạo âm thanh cảnh báo cháy")
                return None

            if base64_audio:
                self._alert_audio_base64 = base64_audio
                try:
                    self.alert_audio_path.write_text(base64_audio, encoding="utf-8")
                    logger.debug(
                        "💾 Đã lưu âm thanh cảnh báo cháy tại %s", self.alert_audio_path
                    )
                except OSError:
                    logger.exception(
                        "❌ Không thể lưu âm thanh cảnh báo cháy tại %s", self.alert_audio_path
                    )
            return self._alert_audio_base64


__all__ = ["FireDetectionService", "FireAlertPayload"]

