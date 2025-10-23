"""Utility script to pre-generate the fire alert audio clip."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path


def _ensure_backend_on_path() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))


_ensure_backend_on_path()

from app.core.config import settings  # noqa: E402  pylint: disable=wrong-import-position
from app.services.notification_voice_service import (  # noqa: E402  pylint: disable=wrong-import-position
    NotificationVoiceService,
)


async def generate_fire_alert_audio(output: Path, text: str) -> None:
    service = NotificationVoiceService()
    audio_base64 = await service.generate_voice_notification_base64(text)
    if not audio_base64:
        print("Không thể tạo âm thanh cảnh báo cháy", file=sys.stderr)
        sys.exit(1)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(audio_base64, encoding="utf-8")
    print(f"✅ Đã lưu âm thanh cảnh báo cháy tại {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Tạo trước âm thanh cảnh báo cháy")
    parser.add_argument(
        "--output",
        type=Path,
        default=settings.fire_alert_audio_file,
        help="Đường dẫn file .b64 để lưu",
    )
    parser.add_argument(
        "--text",
        default="Cảnh báo cháy! Vui lòng kiểm tra khu vực ngay lập tức.",
        help="Thông điệp sẽ được đọc khi phát cảnh báo",
    )
    args = parser.parse_args()

    asyncio.run(generate_fire_alert_audio(args.output, args.text))


if __name__ == "__main__":
    main()

