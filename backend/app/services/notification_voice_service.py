import base64
import base64
import logging
import struct
from typing import Optional

from google import genai
from google.genai import types

from app.core.config import settings


logger = logging.getLogger(__name__)


class NotificationVoiceService:
    """Generate fire-alert notifications using Gemini Live when available."""

    SAMPLE_RATE = 24000
    DURATION_SECONDS = 1

    def __init__(
        self,
        client: Optional[genai.Client] = None,
        model: Optional[str] = None,
        voice_name: str = "Aoede",
        language_code: str = "vi-VN",
    ) -> None:
        self.client = client
        if self.client is None and settings.google_api_key:
            self.client = genai.Client(api_key=settings.google_api_key)
        self.model = model or settings.gemini_model
        self.voice_name = voice_name
        self.language_code = language_code

    async def generate_voice_notification_base64(self, text: str) -> Optional[str]:
        normalized_text = text.strip()
        if not normalized_text:
            return None

        base64_audio = await self._generate_via_gemini(normalized_text)
        if base64_audio:
            return base64_audio

        logger.info("Falling back to synthetic tone for voice notification")
        return self._generate_fallback_tone()

    async def _generate_via_gemini(self, text: str) -> Optional[str]:
        if not self.client:
            logger.warning("Google API key not configured; skipping Gemini voice synthesis")
            return None

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=[types.Content(role="user", parts=[types.Part(text=text)])],
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=self.voice_name
                            )
                        ),
                        language_code=self.language_code,
                    ),
                ),
            )
        except Exception:  # pylint: disable=broad-except
            logger.exception("Failed to call Gemini for voice notification")
            return None

        audio_bytes = self._extract_audio_bytes(response)
        if not audio_bytes:
            logger.warning("Gemini response did not include audio data for voice notification")
            return None

        return base64.b64encode(audio_bytes).decode("utf-8")

    def _extract_audio_bytes(self, response: types.GenerateContentResponse) -> Optional[bytes]:
        for candidate in response.candidates or []:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            for part in getattr(content, "parts", []) or []:
                inline_data = getattr(part, "inline_data", None)
                if inline_data and getattr(inline_data, "data", None):
                    return inline_data.data
        return None

    def _generate_fallback_tone(self) -> str:
        frame_count = self.SAMPLE_RATE * self.DURATION_SECONDS
        amplitude = 8000
        samples = bytearray()
        for i in range(frame_count):
            value = int(amplitude * (i % 32) / 31)
            samples.extend(struct.pack("<h", value))
        return base64.b64encode(bytes(samples)).decode("utf-8")
