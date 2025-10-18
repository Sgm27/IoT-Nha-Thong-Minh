import base64
import struct
from typing import Optional


class NotificationVoiceService:
    """Simple voice notification generator.

    The original project uses the Gemini API to synthesise speech. To keep the
    testing surface small and avoid network calls we generate a short PCM tone
    that the client can play as a notification sound.
    """

    SAMPLE_RATE = 16000
    DURATION_SECONDS = 1

    async def generate_voice_notification_base64(self, text: str) -> Optional[str]:
        del text  # The lightweight implementation produces a generic tone.
        frame_count = self.SAMPLE_RATE * self.DURATION_SECONDS
        amplitude = 8000
        samples = bytearray()
        for i in range(frame_count):
            value = int(amplitude * (i % 32) / 31)  # Saw wave to keep simple
            samples.extend(struct.pack("<h", value))
        return base64.b64encode(bytes(samples)).decode("utf-8")
