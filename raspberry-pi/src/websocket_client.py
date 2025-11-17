"""
WebSocket Client cho Raspberry Pi 5
Kết nối với backend server để gửi/nhận data
"""

import asyncio
import websockets
import json
import logging
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class WebSocketConfig:
    """Cấu hình WebSocket"""
    server_url: str = "ws://localhost:8000/ws/gemini"
    reconnect_delay: float = 3.0
    ping_interval: float = 10.0
    ping_timeout: float = 30.0


class WebSocketClient:
    """
    WebSocket client để kết nối với backend

    Tự động reconnect khi mất kết nối
    """

    def __init__(self, config: WebSocketConfig):
        """
        Args:
            config: WebSocketConfig object
        """
        self.config = config
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False
        self.connected = False

        # Callbacks
        self.on_light_update: Optional[Callable[[str, bool], None]] = None
        self.on_audio_response: Optional[Callable[[str, int], None]] = None
        self.on_fire_alert: Optional[Callable[[str, str], None]] = None
        self.on_message: Optional[Callable[[Dict[str, Any]], None]] = None

    def set_light_update_callback(self, callback: Callable[[str, bool], None]) -> None:
        """Callback khi nhận lệnh cập nhật đèn (location, is_on)"""
        self.on_light_update = callback

    def set_audio_response_callback(self, callback: Callable[[str, int], None]) -> None:
        """Callback khi nhận audio response (audio_b64, sample_rate)"""
        self.on_audio_response = callback

    def set_fire_alert_callback(self, callback: Callable[[str, str], None]) -> None:
        """Callback khi nhận cảnh báo cháy (message, audio_b64)"""
        self.on_fire_alert = callback

    def set_message_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Callback cho tất cả messages"""
        self.on_message = callback

    async def connect(self) -> bool:
        """
        Kết nối đến WebSocket server

        Returns:
            True nếu thành công
        """
        try:
            logger.info(f"Đang kết nối đến {self.config.server_url}...")

            self.websocket = await websockets.connect(
                self.config.server_url,
                ping_interval=self.config.ping_interval,
                ping_timeout=self.config.ping_timeout,
            )

            self.connected = True
            logger.info("✓ Kết nối WebSocket thành công")
            return True

        except Exception as e:
            logger.error(f"Lỗi kết nối WebSocket: {e}")
            self.connected = False
            return False

    async def disconnect(self) -> None:
        """Ngắt kết nối"""
        if self.websocket is not None:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.error(f"Lỗi khi đóng WebSocket: {e}")

        self.websocket = None
        self.connected = False
        logger.info("Đã ngắt kết nối WebSocket")

    async def send_text(self, text: str) -> bool:
        """
        Gửi text message

        Args:
            text: Nội dung text

        Returns:
            True nếu thành công
        """
        if not self.connected or self.websocket is None:
            logger.warning("WebSocket chưa kết nối")
            return False

        try:
            message = {"text": text}
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Lỗi khi gửi text: {e}")
            return False

    async def send_audio_chunk(self, audio_b64: str, sample_rate: int = 16000) -> bool:
        """
        Gửi audio chunk (PCM16 base64)

        Args:
            audio_b64: Base64 encoded PCM16 audio
            sample_rate: Sample rate (default 16000)

        Returns:
            True nếu thành công
        """
        if not self.connected or self.websocket is None:
            return False

        try:
            message = {
                "realtime_input": {
                    "media_chunks": [
                        {
                            "mime_type": f"audio/pcm;rate={sample_rate}",
                            "data": audio_b64
                        }
                    ]
                }
            }
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Lỗi khi gửi audio chunk: {e}")
            return False

    async def send_camera_frame(self, jpeg_b64: str) -> bool:
        """
        Gửi camera frame (JPEG base64)

        Args:
            jpeg_b64: Base64 encoded JPEG image

        Returns:
            True nếu thành công
        """
        if not self.connected or self.websocket is None:
            return False

        try:
            message = {
                "realtime_input": {
                    "media_chunks": [
                        {
                            "mime_type": "image/jpeg",
                            "data": jpeg_b64
                        }
                    ]
                }
            }
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Lỗi khi gửi camera frame: {e}")
            return False

    async def send_keepalive(self) -> bool:
        """
        Gửi keepalive message

        Returns:
            True nếu thành công
        """
        if not self.connected or self.websocket is None:
            return False

        try:
            import time
            message = {
                "keepalive": {
                    "timestamp": time.time()
                }
            }
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Lỗi khi gửi keepalive: {e}")
            return False

    async def receive_loop(self) -> None:
        """Main loop để nhận messages từ server"""
        while self.running:
            if not self.connected or self.websocket is None:
                # Chờ reconnect
                await asyncio.sleep(1.0)
                continue

            try:
                # Nhận message
                message_str = await self.websocket.recv()
                message = json.loads(message_str)

                # Gọi message callback
                if self.on_message:
                    self.on_message(message)

                # Process message
                await self._process_message(message)

            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed")
                self.connected = False
                # Auto reconnect
                await asyncio.sleep(self.config.reconnect_delay)
                await self.connect()

            except Exception as e:
                logger.error(f"Lỗi khi nhận message: {e}")
                await asyncio.sleep(0.1)

    async def _process_message(self, message: Dict[str, Any]) -> None:
        """
        Xử lý message từ server

        Args:
            message: Message dict
        """
        try:
            # Light update
            if message.get("type") == "smart_home_light_update":
                location = message.get("location", "")
                is_on = message.get("is_on", False)
                if self.on_light_update:
                    self.on_light_update(location, is_on)

            # Audio response
            elif "audio" in message:
                audio_data = message["audio"]
                if isinstance(audio_data, dict):
                    audio_b64 = audio_data.get("data", "")
                    sample_rate = audio_data.get("sample_rate", 16000)
                else:
                    audio_b64 = audio_data
                    sample_rate = 16000

                if self.on_audio_response and audio_b64:
                    self.on_audio_response(audio_b64, sample_rate)

            # Fire alert
            elif message.get("type") == "fire_detection_alert":
                alert_message = message.get("message", "")
                audio_b64 = message.get("audio_base64", "")
                if self.on_fire_alert:
                    self.on_fire_alert(alert_message, audio_b64)

            # Text message
            elif "text" in message:
                text = message.get("text", "")
                logger.info(f"[Server] {text}")

            # Transcription
            elif "transcription" in message:
                trans = message["transcription"]
                sender = trans.get("sender", "Unknown")
                text = trans.get("text", "")
                finished = trans.get("finished", False)
                if finished:
                    logger.info(f"[{sender}] {text}")

        except Exception as e:
            logger.error(f"Lỗi khi xử lý message: {e}")

    async def run(self) -> None:
        """
        Chạy WebSocket client với auto-reconnect

        Chạy receive loop và tự động reconnect khi mất kết nối
        """
        self.running = True

        # Kết nối lần đầu
        await self.connect()

        # Chạy receive loop
        await self.receive_loop()

    def stop(self) -> None:
        """Dừng WebSocket client"""
        self.running = False
        logger.info("WebSocket client đã dừng")
