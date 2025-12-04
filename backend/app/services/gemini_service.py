"""Gemini Live WebSocket service tailored for the smart home assistant."""

from __future__ import annotations

import asyncio
import base64
import binascii
import datetime as dt
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from fastapi import WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types

from app.core.config import settings
from app.services.face_recognition_service import FaceRecognitionService, get_face_recognition_service
from app.services.fire_detection_service import FireDetectionService
from app.services.notification_voice_service import NotificationVoiceService
from app.services.session_service import SessionService
from app.services.smart_home_service import SmartHomeService, get_smart_home_service

logger = logging.getLogger(__name__)


class GeminiService:
    """Service orchestrating the bi-directional Gemini Live conversation."""

    SYSTEM_INSTRUCTION = """
    Bạn là trợ lý AI cho hệ thống nhà thông minh IoT Nha Thong Minh. Hãy trò chuyện tự nhiên,
    thân thiện và sử dụng tiếng Việt. Bạn có thể nhận yêu cầu bằng giọng nói, văn bản hoặc
    hình ảnh. Khi người dùng yêu cầu thao tác với thiết bị trong nhà, hãy GỌI TOOL phù hợp
    NGAY LẬP TỨC trước khi trả lời họ. Các tool bạn có thể sử dụng:
    - turn_on_light: bật đèn ở một vị trí bất kỳ
    - turn_off_light: tắt đèn ở một vị trí bất kỳ
    - play_music: phát bài hát gần giống nhất với tên được yêu cầu
    - pause_music: tạm dừng bài hát đang phát
    - continue_music: tiếp tục phát bài hát đã tạm dừng
    - control_motor: điều khiển motor/quạt (bật, tắt, điều chỉnh tốc độ)
    - control_door: mở hoặc đóng cửa bằng servo motor

    Quy tắc sử dụng tool:
    1. Nếu người dùng nhắc đến bật đèn, chiếu sáng, sáng đèn,... hãy gọi tool turn_on_light.
    2. Nếu người dùng nhắc đến tắt đèn, dập đèn,... hãy gọi tool turn_off_light.
    3. Nếu người dùng muốn nghe nhạc, hãy gọi tool play_music và truyền tên bài hát họ nêu ra.
    4. Nếu người dùng yêu cầu tạm dừng nhạc, hãy gọi tool pause_music.
    5. Nếu người dùng yêu cầu bật lại nhạc đã tạm dừng, hãy gọi tool continue_music.
    6. Nếu người dùng nhắc đến bật quạt, mở quạt, chạy quạt,... hãy gọi tool control_motor với action "on".
    7. Nếu người dùng nhắc đến tắt quạt, dừng quạt,... hãy gọi tool control_motor với action "off".
    8. Nếu người dùng muốn điều chỉnh tốc độ quạt (chậm, nhanh, mạnh, nhẹ,...) hãy gọi tool control_motor với speed phù hợp.
    9. Nếu người dùng nhắc đến mở cửa, mở cổng,... hãy gọi tool control_door với action "open".
    10. Nếu người dùng nhắc đến đóng cửa, đóng cổng, khép cửa,... hãy gọi tool control_door với action "close".

    Khi xử lý hình ảnh, mô tả chi tiết nội dung ảnh và liên hệ với ngữ cảnh căn nhà.
    Khi trả lời, hãy chia nhỏ nội dung thành các mục rõ ràng, dễ hiểu.
    """

    def __init__(
        self,
        client: Optional[genai.Client] = None,
        model: Optional[str] = None,
        session_service: Optional[SessionService] = None,
        smart_home_service: Optional[SmartHomeService] = None,
        notification_voice_service: Optional[NotificationVoiceService] = None,
        fire_detection_service: Optional[FireDetectionService] = None,
        face_recognition_service: Optional[FaceRecognitionService] = None,
        history_file: Optional[Path] = None,
    ) -> None:
        self.client = client
        if self.client is None and settings.google_api_key:
            self.client = genai.Client(api_key=settings.google_api_key)
        self.model = model or settings.gemini_model
        self.session_service = session_service or SessionService()
        self.smart_home_service = smart_home_service or get_smart_home_service()
        self.notification_voice_service = (
            notification_voice_service or NotificationVoiceService()
        )
        self.fire_detection_service = fire_detection_service or FireDetectionService(
            notification_voice_service=self.notification_voice_service
        )
        self.face_recognition_service = face_recognition_service or get_face_recognition_service()

        self.conversation_history_file: Path = history_file or settings.conversation_history_file
        self.conversation_history_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.conversation_history_file.exists():
            self.conversation_history_file.write_text("[]", encoding="utf-8")

        self._captured_images_dir: Path = settings.captured_images_directory
        self._capture_interval_seconds: float = settings.capture_interval_seconds
        if settings.save_captured_image:
            self._captured_images_dir.mkdir(parents=True, exist_ok=True)

        self._current_user_input = ""
        self._current_assistant_output = ""
        self._send_locks: Dict[WebSocket, asyncio.Lock] = {}
        self._default_output_sample_rate = 24000
        self._latest_session_handle: Optional[str] = None
        self._latest_token_usage: Optional[Dict[str, int]] = None

        # Door control state
        self._last_door_open_time: float = 0.0
        self._door_open_cooldown_seconds: float = 30.0  # Cooldown between door opens (30s)
        self._door_auto_close_seconds: float = 5.0  # Auto close after this many seconds

        # Face recognition throttling - avoid calling API too often
        self._last_face_recognition_time: float = 0.0
        self._face_recognition_interval_seconds: float = 3.0  # Only check face every 3 seconds

    # ------------------------------------------------------------------
    # WebSocket orchestration
    # ------------------------------------------------------------------
    async def handle_websocket_connection(self, websocket: WebSocket) -> None:
        """Main entry point for the Gemini WebSocket connection."""

        previous_session_handle = self.session_service.load_previous_session_handle()
        self._latest_session_handle = previous_session_handle
        self._latest_token_usage = self._sanitize_token_usage(
            self.session_service.get_last_token_usage()
        )
        await self._send_safely(
            websocket,
            {
                "setupComplete": {
                    "cameraCaptureIntervalSeconds": self._capture_interval_seconds,
                    "cameraCaptureIntervalMs": int(self._capture_interval_seconds * 1000),
                }
            },
        )

        if not self.client:
            logger.warning("Google API key is missing. Running in offline echo mode.")
            await self._run_offline_loop(websocket)
            return

        config = self._create_live_config(previous_session_handle)

        send_task = receive_task = ping_task = light_task = None
        fallback_message: Optional[Dict[str, Any]] = None
        try:
            async with self.client.aio.live.connect(model=self.model, config=config) as session:
                send_task = asyncio.create_task(
                    self._relay_client_to_gemini(websocket, session)
                )
                receive_task = asyncio.create_task(
                    self._relay_gemini_to_client(websocket, session)
                )
                ping_task = asyncio.create_task(self._ping_websocket(websocket))
                light_task = asyncio.create_task(self._forward_light_updates(websocket))

                done, pending = await asyncio.wait(
                    [send_task, receive_task, ping_task, light_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
                for task in done:
                    task.result()
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected by client")
        except TimeoutError as exc:
            logger.error("Gemini connection timed out during handshake: %s", exc)
            fallback_message = {
                "type": "connection_error",
                "code": "gemini_handshake_timeout",
                "message": "Không thể kết nối tới Gemini (timeout). Ứng dụng sẽ chuyển sang chế độ ngoại tuyến.",
            }
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Gemini session failed: %s", exc)
            fallback_message = {
                "type": "connection_error",
                "code": "gemini_session_error",
                "message": "Gemini gặp sự cố khi thiết lập phiên. Ứng dụng sẽ chuyển sang chế độ ngoại tuyến.",
            }
        finally:
            for task in filter(None, [send_task, receive_task, ping_task, light_task]):
                if not task.done():
                    task.cancel()
            if fallback_message and websocket.client_state.name == "CONNECTED":
                await self._send_safely(websocket, fallback_message)
                await self._run_offline_loop(websocket)
            self._send_locks.pop(websocket, None)

    async def _run_offline_loop(self, websocket: WebSocket) -> None:
        """Fallback mode used during tests when Gemini credentials are absent."""

        async def receive_messages():
            try:
                while True:
                    data = await websocket.receive_text()
                    payload = json.loads(data)
                    if "text" in payload:
                        text = payload["text"]
                        await self._send_safely(websocket, {"text": f"(offline) {text}"})
                    elif "tool_call" in payload:
                        await self._handle_tool_calls(websocket, None, payload["tool_call"])
            except WebSocketDisconnect:
                logger.info("Offline loop websocket disconnect")

        # Run message receiver and light update forwarder in parallel
        receive_task = asyncio.create_task(receive_messages())
        light_task = asyncio.create_task(self._forward_light_updates(websocket))

        try:
            done, pending = await asyncio.wait(
                [receive_task, light_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
        finally:
            for task in [receive_task, light_task]:
                if not task.done():
                    task.cancel()

    # ------------------------------------------------------------------
    # Gemini streaming relays
    # ------------------------------------------------------------------
    async def _relay_client_to_gemini(self, websocket: WebSocket, session) -> None:
        logger.info("🚀 Client -> Gemini relay started")
        try:
            while True:
                try:
                    message = await asyncio.wait_for(
                        websocket.receive_text(), timeout=settings.websocket_receive_timeout
                    )
                except asyncio.TimeoutError:
                    logger.debug(
                        "⏳ No client message received in %s seconds; continuing to listen",
                        settings.websocket_receive_timeout,
                    )
                    continue

                data = json.loads(message)
                logger.debug(f"📥 Received from client: {list(data.keys())}")

                if "keepalive" in data:
                    await self._send_safely(
                        websocket,
                        {
                            "type": "keepalive_response",
                            "timestamp": dt.datetime.utcnow().isoformat(),
                        },
                    )
                    continue

                if "realtime_input" in data:
                    realtime_input = data["realtime_input"]
                    if isinstance(realtime_input, dict):
                        media_chunks = realtime_input.get("media_chunks", [])
                        if isinstance(media_chunks, list):
                            for chunk in media_chunks:
                                if isinstance(chunk, dict):
                                    await self._process_realtime_media_chunk(
                                        websocket, session, chunk
                                    )
                    continue

                if "text" in data:
                    text_content = data["text"]
                    logger.info(f"📝 Sending text to Gemini: {text_content}")
                    await session.send_client_content(
                        turns={"role": "user", "parts": [{"text": text_content}]},
                        turn_complete=True,
                    )
                    self._append_to_conversation_history("user", text_content)
                    logger.info("✅ Text sent and saved to history")
                    continue

                if "voice_notification_request" in data:
                    await self._handle_voice_notification_request(
                        websocket, data["voice_notification_request"]
                    )
                    continue

                # Handle hardware fire alerts from IoT client (flame sensor module)
                if data.get("type") == "hardware_fire_alert":
                    await self._handle_hardware_fire_alert(websocket, data)
                    continue
        except WebSocketDisconnect:
            logger.info("Client disconnected (send loop)")
        except asyncio.CancelledError:
            logger.info("Client -> Gemini relay cancelled")
            raise
        except Exception:
            logger.exception("❌ Unexpected error in client relay loop")
        finally:
            logger.info("Client -> Gemini relay stopped")

    def _persist_session_handle(
        self,
        handle: Optional[str],
        *,
        token_usage: Optional[Dict[str, int]] = None,
        force: bool = False,
    ) -> None:
        """Persist the resumable session handle when available."""
        if not handle:
            return

        if not force and handle == self._latest_session_handle:
            return

        self._latest_session_handle = handle
        if token_usage is not None:
            self._latest_token_usage = self._sanitize_token_usage(token_usage)

        try:
            self.session_service.save_previous_session_handle(
                handle, token_usage=self._latest_token_usage
            )
            logger.info("💾 Đã lưu session handle để phục hồi lần sau")
        except Exception as exc:
            logger.exception("❌ Không thể lưu session handle: %s", exc)

    @staticmethod
    def _sanitize_token_usage(
        usage: Optional[Dict[str, object]]
    ) -> Optional[Dict[str, int]]:
        if not usage:
            return None
        sanitized: Dict[str, int] = {}
        for key, value in usage.items():
            if isinstance(value, (int, float)):
                sanitized[key] = int(value)
        return sanitized or None

    @staticmethod
    def _extract_token_usage(metadata) -> Optional[Dict[str, int]]:
        if metadata is None:
            return None
        raw_usage: Dict[str, object]
        try:
            raw_usage = metadata.model_dump(exclude_none=True)  # type: ignore[attr-defined]
        except AttributeError:
            raw_usage = {}
            for attr in (
                "total_token_count",
                "input_token_count",
                "output_token_count",
                "input_token_count_total",
                "output_token_count_total",
            ):
                value = getattr(metadata, attr, None)
                if value is not None:
                    raw_usage[attr] = value
        return GeminiService._sanitize_token_usage(raw_usage)

    async def _relay_gemini_to_client(self, websocket: WebSocket, session) -> None:
        try:
            while True:
                try:
                    async for response in session.receive():
                        # Check if WebSocket is still connected before processing
                        if hasattr(websocket, 'client_state') and websocket.client_state.name != 'CONNECTED':
                            logger.warning("⚠️ WebSocket not connected, stopping receive")
                            break
                        
                        if hasattr(response, "tool_call") and response.tool_call:
                            await self._handle_tool_calls(websocket, session, response.tool_call)
                            continue

                        if getattr(response, "usage_metadata", None):
                            usage_snapshot = self._extract_token_usage(response.usage_metadata)
                            if usage_snapshot:
                                self._latest_token_usage = usage_snapshot
                                logger.info(
                                    "🔢 Token usage - total: %s | input: %s | output: %s",
                                    usage_snapshot.get("total_token_count"),
                                    usage_snapshot.get("input_token_count"),
                                    usage_snapshot.get("output_token_count"),
                                )

                        if response.server_content and response.server_content.output_transcription:
                            transcription = response.server_content.output_transcription
                            if transcription.text:
                                self._current_assistant_output += transcription.text
                                logger.info("Gemini transcript chunk:\n%s", transcription.text)
                            await self._send_safely(
                                websocket,
                                {
                                    "transcription": {
                                        "text": transcription.text,
                                        "sender": "Gemini",
                                        "finished": transcription.finished,
                                    }
                                },
                            )
                            if transcription.finished and self._current_assistant_output.strip():
                                logger.info(
                                    "Gemini full transcript:\n%s",
                                    self._current_assistant_output.strip(),
                                )
                                self._append_to_conversation_history(
                                    "assistant", self._current_assistant_output.strip()
                                )
                                self._current_assistant_output = ""

                        if response.server_content and response.server_content.input_transcription:
                            transcription = response.server_content.input_transcription
                            if transcription.text:
                                self._current_user_input += transcription.text
                                logger.info("🎤 User transcript chunk: %s", transcription.text)
                            await self._send_safely(
                                websocket,
                                {
                                    "transcription": {
                                        "text": transcription.text,
                                        "sender": "User",
                                        "finished": transcription.finished,
                                    }
                                },
                            )
                            if transcription.finished and self._current_user_input.strip():
                                logger.info(
                                    "🎤✅ User full transcript (FINISHED):\n%s",
                                    self._current_user_input.strip(),
                                )
                                logger.info("🔄 User đã nói xong, Gemini sẽ bắt đầu xử lý...")
                                self._append_to_conversation_history(
                                    "user", self._current_user_input.strip()
                                )
                                self._current_user_input = ""

                        if response.server_content and response.server_content.model_turn:
                            for part in response.server_content.model_turn.parts:
                                if getattr(part, "text", None):
                                    await self._send_safely(websocket, {"text": part.text})
                                if getattr(part, "inline_data", None):
                                    await self._enqueue_audio_chunk(websocket, part.inline_data)

                        if response.session_resumption_update:
                            update = response.session_resumption_update
                            self._persist_session_handle(
                                getattr(update, "new_handle", None),
                                token_usage=self._latest_token_usage,
                            )

                        if response.server_content and response.server_content.turn_complete:
                            logger.info("\n<Turn complete>")
                            logger.info("=" * 50)
                            logger.info("🎯 Turn hoàn thành, sẵn sàng nhận input tiếp theo")

                            # Ensure latest resumable session state is flushed to disk
                            self._persist_session_handle(
                                self._latest_session_handle,
                                token_usage=self._latest_token_usage,
                                force=True,
                            )
                            
                            # Send turn complete signal to client
                            await self._send_safely(
                                websocket,
                                {
                                    "transcription": {
                                        "text": "",
                                        "sender": "Gemini",
                                        "finished": True
                                    }
                                },
                            )
                            logger.info("✅ Đã gửi tín hiệu turn_complete về client")
                            
                            # Persist any remaining buffered texts at end of turn
                            if self._current_user_input.strip():
                                self._append_to_conversation_history(
                                    "user", self._current_user_input.strip()
                                )
                                self._current_user_input = ""
                                logger.info("💾 Đã lưu user input vào lịch sử")
                            
                            if self._current_assistant_output.strip():
                                self._append_to_conversation_history(
                                    "assistant", self._current_assistant_output.strip()
                                )
                                self._current_assistant_output = ""
                                logger.info("💾 Đã lưu assistant output vào lịch sử")
                
                except WebSocketDisconnect:
                    logger.info("WebSocket disconnected during receive")
                    break
                except Exception as e:
                    logger.error(f"❌ Error processing Gemini response: {e}")
                    logger.exception("Full traceback:")
                    # Break on error to exit while loop
                    break
                    
        except WebSocketDisconnect:
            logger.info("Client disconnected (receive loop)")
        except asyncio.CancelledError:
            logger.info("Receive task cancelled")
        except Exception as e:
            logger.error(f"❌ Fatal error in receive loop: {e}")
            logger.exception("Full traceback:")
        finally:
            logger.info("Gemini -> Client relay stopped")

    async def _enqueue_audio_chunk(self, websocket: WebSocket, inline_data) -> None:
        if not inline_data or not getattr(inline_data, "data", None):
            return

        try:
            audio_data = inline_data.data
            base64_audio = base64.b64encode(audio_data).decode("utf-8")
            await self._send_safely(websocket, {"audio": base64_audio})
        except (TypeError, ValueError, binascii.Error) as e:
            logger.error(f"Error processing assistant audio: {e}")

    async def _ping_websocket(self, websocket: WebSocket) -> None:
        try:
            while True:
                await asyncio.sleep(settings.websocket_ping_interval)
                await self._send_safely(
                    websocket,
                    {
                        "type": "keepalive",
                        "timestamp": dt.datetime.utcnow().isoformat(),
                    },
                )
        except WebSocketDisconnect:
            logger.info("Ping loop stopped (disconnect)")

    async def _forward_light_updates(self, websocket: WebSocket) -> None:
        """Subscribe to lighting service updates and forward them to WebSocket client."""
        queue = None
        try:
            # Subscribe to lighting service updates
            queue = await self.smart_home_service.lighting_service.add_listener()
            logger.info("🔦 Subscribed to lighting service updates")

            while True:
                # Wait for update from lighting service
                update = await queue.get()

                # Forward to WebSocket client
                if update.get("type") == "update":
                    light_data = update.get("light", {})
                    await self._send_safely(
                        websocket,
                        {
                            "type": "smart_home_light_update",
                            "location": light_data.get("location", ""),
                            "is_on": light_data.get("is_on", False),
                        },
                    )
                    logger.info(
                        "Forwarded light update: %s = %s",
                        light_data.get("location"),
                        "ON" if light_data.get("is_on") else "OFF"
                    )
                elif update.get("type") == "motor_control":
                    await self._send_safely(websocket, update)
                    logger.info(
                        "Forwarded motor control: %s → %s",
                        update.get("name"),
                        update.get("action")
                    )
                elif update.get("type") == "door_control":
                    await self._send_safely(websocket, update)
                    logger.info(
                        "Forwarded door control: %s → %s (angle: %s°)",
                        update.get("name"),
                        update.get("action"),
                        update.get("angle")
                    )
                elif update.get("type") == "hardware_fire_alert":
                    # Forward hardware fire alert to all connected clients
                    await self._send_safely(
                        websocket,
                        {
                            "type": "fire_detection_alert",
                            "source": "hardware_sensor",
                            "sensor_name": update.get("sensor_name", "Unknown"),
                            "level": update.get("level", "warning"),
                            "message": update.get("message", ""),
                            "consecutive_count": update.get("consecutive_count", 0),
                            "timestamp": update.get("timestamp", ""),
                        },
                    )
                    logger.warning(
                        "🔥 Forwarded hardware fire alert: %s (level: %s)",
                        update.get("sensor_name"),
                        update.get("level")
                    )
        except WebSocketDisconnect:
            logger.info("Light update forwarding stopped (disconnect)")
        finally:
            # Cleanup: remove listener
            if queue is not None:
                self.smart_home_service.lighting_service.remove_listener(queue)

    async def _process_realtime_media_chunk(
        self, websocket: WebSocket, session, chunk: Dict[str, Any]
    ) -> None:
        """Decode realtime media payloads from the client and forward them to Gemini."""

        mime = chunk.get("mime_type")
        payload = chunk.get("data")

        if not isinstance(mime, str) or not payload:
            return

        payload_bytes: Optional[bytes]
        if isinstance(payload, str):
            try:
                payload_bytes = base64.b64decode(payload)
            except (ValueError, binascii.Error):
                logger.warning("Không thể giải mã dữ liệu realtime_input")
                return
        elif isinstance(payload, (bytes, bytearray)):
            payload_bytes = bytes(payload)
        else:
            return

        normalized_mime = mime.lower()
        blob = types.Blob(data=payload_bytes, mime_type=mime)
        audio_blob = blob if normalized_mime.startswith("audio/") else None
        media_blob = blob if normalized_mime.startswith("image/") else None

        # Log image receipt
        if media_blob:
            logger.info(f"📷 Received camera frame: {len(payload_bytes)} bytes, mime={mime}")

        if media_blob and settings.save_captured_image:
            try:
                self._save_captured_image(payload_bytes, mime)
            except Exception:  # pylint: disable=broad-except
                logger.exception("❌ Không thể lưu ảnh từ realtime_input")

        if not audio_blob and not media_blob:
            logger.debug("Bỏ qua realtime_input với mime type không hỗ trợ: %s", mime)
            return

        # Fire detection and face recognition run in parallel, independent of Gemini connection
        if media_blob:
            await asyncio.gather(
                self._maybe_handle_fire_detection(websocket, payload_bytes, normalized_mime),
                self._maybe_handle_face_recognition(websocket, payload_bytes),
                return_exceptions=True,
            )

        # Then send to Gemini (may fail if offline)
        try:
            await session.send_realtime_input(audio=audio_blob, media=media_blob)
        except Exception as e:
            logger.warning(f"Could not send to Gemini (offline mode?): {e}")

    async def _maybe_handle_fire_detection(
        self, websocket: WebSocket, data: bytes, mime: str
    ) -> None:
        if not self.fire_detection_service:
            logger.warning("Fire detection service not available")
            return

        logger.debug(f"🔥 Processing image for fire detection ({len(data)} bytes)")

        try:
            payload = await self.fire_detection_service.process_image(data, mime)
        except Exception:  # pylint: disable=broad-except
            logger.exception("❌ Lỗi khi xử lý phát hiện cháy")
            return
        if payload:
            logger.warning(f"🚨 FIRE ALERT PAYLOAD READY - sending to client")
            await self._send_safely(websocket, payload)

    async def _maybe_handle_face_recognition(self, websocket: WebSocket, data: bytes) -> None:
        """Process image for face recognition against host faces.

        When host face is detected, automatically opens the door via servo.
        Includes cooldown to prevent multiple opens and auto-close after delay.
        """
        if not self.face_recognition_service:
            return

        if not self.face_recognition_service.is_enabled:
            return

        current_time = time.time()

        # Throttle face recognition API calls - only process every N seconds
        time_since_last_check = current_time - self._last_face_recognition_time
        if time_since_last_check < self._face_recognition_interval_seconds:
            return

        # Also skip if door was recently opened (during cooldown)
        time_since_door_open = current_time - self._last_door_open_time
        if time_since_door_open < self._door_open_cooldown_seconds:
            logger.debug(
                f"Door cooldown active ({time_since_door_open:.1f}s / {self._door_open_cooldown_seconds}s), skipping face recognition"
            )
            return

        # Update last check time BEFORE calling API
        self._last_face_recognition_time = current_time

        logger.debug(f"👤 Processing image for face recognition ({len(data)} bytes)")

        try:
            result = await self.face_recognition_service.process_image(data)

            # If host face detected, open the door
            if result.get("is_host_detected"):
                matched_host = result.get("matched_host", "Unknown")
                confidence = result.get("confidence", 0.0)

                self._last_door_open_time = current_time

                logger.info(
                    f"🚪 Nhận diện chủ nhà thành công: {matched_host} (confidence: {confidence:.2f}%) - Mở cửa!"
                )

                # Notify IoT client to open door via LightingService observer
                self.smart_home_service.lighting_service.notify_door_control(
                    device="Cửa",
                    action="open",
                    angle=90.0,  # Full open
                )

                # Send notification to frontend
                await self._send_safely(websocket, {
                    "type": "face_recognition_result",
                    "is_host_detected": True,
                    "matched_host": matched_host,
                    "confidence": confidence,
                    "door_action": "open",
                })

                # Schedule auto-close after delay
                asyncio.create_task(self._auto_close_door(websocket))

        except Exception:  # pylint: disable=broad-except
            logger.exception("❌ Lỗi khi xử lý nhận diện khuôn mặt")

    async def _auto_close_door(self, websocket: WebSocket) -> None:
        """Automatically close the door after a delay."""
        await asyncio.sleep(self._door_auto_close_seconds)

        logger.info(f"🚪 Tự động đóng cửa sau {self._door_auto_close_seconds}s")

        # Notify IoT client to close door
        self.smart_home_service.lighting_service.notify_door_control(
            device="Cửa",
            action="close",
            angle=0.0,
        )

        # Send notification to frontend
        await self._send_safely(websocket, {
            "type": "door_auto_closed",
            "door_action": "close",
        })

    def _save_captured_image(self, data: bytes, mime: str) -> None:
        extension = self._infer_extension_from_mime(mime)
        timestamp = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%S_%f")
        filename = f"capture_{timestamp}{extension}"
        filepath = self._captured_images_dir / filename
        filepath.write_bytes(data)
        logger.debug("💾 Đã lưu ảnh chụp từ camera tại %s", filepath)

    @staticmethod
    def _infer_extension_from_mime(mime: str) -> str:
        subtype = mime.split("/")[-1].lower()
        if subtype in {"jpeg", "jpg"}:
            return ".jpg"
        if subtype == "png":
            return ".png"
        if subtype == "gif":
            return ".gif"
        if subtype in {"bmp", "bitmap"}:
            return ".bmp"
        if subtype == "webp":
            return ".webp"
        return ".bin"

    # ------------------------------------------------------------------
    # Tool handling
    # ------------------------------------------------------------------
    async def _handle_tool_calls(self, websocket: WebSocket, session, tool_call) -> None:
        if not getattr(tool_call, "function_calls", None):
            return

        responses = []
        for function_call in tool_call.function_calls:
            name = function_call.name
            args = getattr(function_call, "args", {}) or {}

            if name == "turn_on_light":
                location = args.get("location", "")
                state = self.smart_home_service.turn_on_light(location)
                await self._send_safely(
                    websocket,
                    {
                        "type": "smart_home_light_update",
                        "location": state.location,
                        "is_on": state.is_on,
                    },
                )
                responses.append(
                    types.FunctionResponse(
                        id=function_call.id,
                        name=name,
                        response={
                            "result": "success",
                            "location": state.location,
                            "state": "on",
                        },
                    )
                )

            elif name == "turn_off_light":
                location = args.get("location", "")
                state = self.smart_home_service.turn_off_light(location)
                await self._send_safely(
                    websocket,
                    {
                        "type": "smart_home_light_update",
                        "location": state.location,
                        "is_on": state.is_on,
                    },
                )
                responses.append(
                    types.FunctionResponse(
                        id=function_call.id,
                        name=name,
                        response={
                            "result": "success",
                            "location": state.location,
                            "state": "off",
                        },
                    )
                )

            elif name == "play_music":
                title = args.get("title", "")
                matched = self.smart_home_service.play_music(title)
                stream_url = None
                if matched:
                    file_path = self.smart_home_service.get_song_file(matched)
                    if file_path:
                        stream_url = f"/smart-home/music/stream?{urlencode({'title': matched})}"
                if matched:
                    payload = {
                        "result": "success",
                        "requested_title": title,
                        "matched_song": matched,
                        "stream_url": stream_url,
                    }
                    await self._send_safely(
                        websocket,
                        {
                            "type": "smart_home_music",
                            "requested_title": title,
                            "matched_song": matched,
                            "stream_url": stream_url,
                        },
                    )
                else:
                    payload = {
                        "result": "not_found",
                        "requested_title": title,
                        "stream_url": None,
                    }
                    await self._send_safely(
                        websocket,
                        {
                            "type": "smart_home_music",
                            "requested_title": title,
                            "matched_song": None,
                            "stream_url": None,
                        },
                    )
                responses.append(
                    types.FunctionResponse(
                        id=function_call.id,
                        name=name,
                        response=payload,
                    )
                )
            elif name == "pause_music":
                paused_song = self.smart_home_service.pause_music()
                state = self.smart_home_service.get_music_playback_state()
                if paused_song:
                    payload = {
                        "result": "success",
                        "requested_title": state.requested_title,
                        "matched_song": state.matched_song,
                        "status": state.status,
                    }
                    await self._send_safely(
                        websocket,
                        {
                            "type": "smart_home_music_control",
                            "action": "pause",
                            "status": "paused",
                            "requested_title": state.requested_title,
                            "matched_song": state.matched_song,
                        },
                    )
                else:
                    payload = {
                        "result": "no_active_song",
                        "requested_title": state.requested_title,
                        "matched_song": state.matched_song,
                        "status": state.status,
                    }
                    await self._send_safely(
                        websocket,
                        {
                            "type": "smart_home_music_control",
                            "action": "pause",
                            "status": "no_active_song",
                        },
                    )
                responses.append(
                    types.FunctionResponse(
                        id=function_call.id,
                        name=name,
                        response=payload,
                    )
                )
            elif name == "continue_music":
                resumed_song = self.smart_home_service.continue_music()
                state = self.smart_home_service.get_music_playback_state()
                if resumed_song:
                    payload = {
                        "result": "success",
                        "requested_title": state.requested_title,
                        "matched_song": state.matched_song,
                        "status": state.status,
                    }
                    await self._send_safely(
                        websocket,
                        {
                            "type": "smart_home_music_control",
                            "action": "continue",
                            "status": "playing",
                            "requested_title": state.requested_title,
                            "matched_song": state.matched_song,
                        },
                    )
                else:
                    payload = {
                        "result": "no_paused_song",
                        "requested_title": state.requested_title,
                        "matched_song": state.matched_song,
                        "status": state.status,
                    }
                    await self._send_safely(
                        websocket,
                        {
                            "type": "smart_home_music_control",
                            "action": "continue",
                            "status": "no_paused_song",
                        },
                    )
                responses.append(
                    types.FunctionResponse(
                        id=function_call.id,
                        name=name,
                        response=payload,
                    )
                )
            elif name == "control_motor":
                device = args.get("device", "Quạt")
                action = args.get("action", "")
                speed = args.get("speed", 1.0)

                # Clamp speed to 0-1 range
                speed = max(0.0, min(1.0, float(speed)))

                logger.info(f"🎮 Gemini điều khiển motor: {device} → {action} (tốc độ {speed*100:.0f}%)")

                # Broadcast motor control to ALL connected clients (including IoT client)
                self.smart_home_service.lighting_service.notify_motor_control(device, action, speed)

                responses.append(
                    types.FunctionResponse(
                        id=function_call.id,
                        name=name,
                        response={
                            "result": "success",
                            "device": device,
                            "action": action,
                            "speed": speed,
                        },
                    )
                )

            elif name == "control_door":
                device = args.get("device", "Cửa")
                action = args.get("action", "")

                # Convert action to servo angle
                # open = 90° (fully open), close = 0° (fully closed)
                angle = 90.0 if action == "open" else 0.0

                logger.info(f"🚪 Gemini điều khiển cửa: {device} → {action} (góc {angle}°)")

                # Broadcast door control to ALL connected clients (including IoT client)
                self.smart_home_service.lighting_service.notify_door_control(device, action, angle)

                responses.append(
                    types.FunctionResponse(
                        id=function_call.id,
                        name=name,
                        response={
                            "result": "success",
                            "device": device,
                            "action": action,
                            "angle": angle,
                        },
                    )
                )

            else:
                responses.append(
                    types.FunctionResponse(
                        id=function_call.id,
                        name=name,
                        response={"result": "error", "message": "Unsupported function"},
                    )
                )

        if session and responses:
            await session.send_tool_response(function_responses=responses)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _create_live_config(self, previous_session_handle: Optional[str]) -> types.LiveConnectConfig:
        session_resumption_cfg = types.SessionResumptionConfig(
            handle=previous_session_handle
        )

        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
                ),
                language_code="vi-VN",
            ),
            tools=[
                types.Tool(
                    function_declarations=[
                        types.FunctionDeclaration(
                            name="turn_on_light",
                            description="Bật đèn tại vị trí được chỉ định",
                            parameters={
                                "type": "object",
                                "properties": {
                                    "location": {
                                        "type": "string",
                                        "description": "Vị trí của đèn cần bật",
                                    }
                                },
                                "required": ["location"],
                            },
                        ),
                        types.FunctionDeclaration(
                            name="turn_off_light",
                            description="Tắt đèn tại vị trí được chỉ định",
                            parameters={
                                "type": "object",
                                "properties": {
                                    "location": {
                                        "type": "string",
                                        "description": "Vị trí của đèn cần tắt",
                                    }
                                },
                                "required": ["location"],
                            },
                        ),
                        types.FunctionDeclaration(
                            name="play_music",
                            description="Phát bài hát gần nhất với tiêu đề yêu cầu",
                            parameters={
                                "type": "object",
                                "properties": {
                                    "title": {
                                        "type": "string",
                                        "description": "Tiêu đề bài hát mà người dùng muốn nghe",
                                    }
                                },
                                "required": ["title"],
                            },
                        ),
                        types.FunctionDeclaration(
                            name="pause_music",
                            description="Tạm dừng bài hát đang phát nếu có",
                            parameters={
                                "type": "object",
                                "properties": {},
                                "required": [],
                            },
                        ),
                        types.FunctionDeclaration(
                            name="continue_music",
                            description="Tiếp tục phát bài hát đã tạm dừng nếu có",
                            parameters={
                                "type": "object",
                                "properties": {},
                                "required": [],
                            },
                        ),
                        types.FunctionDeclaration(
                            name="control_motor",
                            description="Điều khiển motor/quạt (bật, tắt, thay đổi tốc độ)",
                            parameters={
                                "type": "object",
                                "properties": {
                                    "device": {
                                        "type": "string",
                                        "description": "Tên thiết bị motor (mặc định: Quạt)",
                                    },
                                    "action": {
                                        "type": "string",
                                        "enum": ["on", "off", "forward", "backward", "stop"],
                                        "description": "Hành động: on (bật), off (tắt), forward (tiến), backward (lùi), stop (dừng)",
                                    },
                                    "speed": {
                                        "type": "number",
                                        "description": "Tốc độ từ 0.0 đến 1.0 (0% đến 100%). Mặc định 1.0. Ví dụ: chậm=0.3, trung bình=0.6, nhanh/mạnh=1.0",
                                    },
                                },
                                "required": ["action"],
                            },
                        ),
                        types.FunctionDeclaration(
                            name="control_door",
                            description="Mở hoặc đóng cửa bằng servo motor",
                            parameters={
                                "type": "object",
                                "properties": {
                                    "device": {
                                        "type": "string",
                                        "description": "Tên cửa cần điều khiển (mặc định: Cửa)",
                                    },
                                    "action": {
                                        "type": "string",
                                        "enum": ["open", "close"],
                                        "description": "Hành động: open (mở cửa), close (đóng cửa)",
                                    },
                                },
                                "required": ["action"],
                            },
                        ),
                    ],
                )
            ],
            system_instruction=self.SYSTEM_INSTRUCTION,
            session_resumption=session_resumption_cfg,
            output_audio_transcription=types.AudioTranscriptionConfig(),
            input_audio_transcription=types.AudioTranscriptionConfig(),
            temperature=0.6,
            top_p=0.85,
        )

    def _append_to_conversation_history(self, role: str, text: str) -> None:
        try:
            history = json.loads(self.conversation_history_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            history = []
        history.append(
            {
                "role": role,
                "text": text,
                "timestamp": dt.datetime.utcnow().isoformat(),
            }
        )
        self.conversation_history_file.write_text(
            json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    async def _handle_voice_notification_request(self, websocket: WebSocket, request: dict) -> None:
        notification_text = request.get("text", "")
        request_id = request.get("request_id", "")
        if not notification_text:
            await self._send_safely(
                websocket,
                {
                    "type": "voice_notification_response",
                    "success": False,
                    "error": "Notification text is required",
                    "request_id": request_id,
                },
            )
            return
        audio_base64 = await self.notification_voice_service.generate_voice_notification_base64(
            notification_text
        )
        await self._send_safely(
            websocket,
            {
                "type": "voice_notification_response",
                "success": True,
                "data": {
                    "notification_text": notification_text,
                    "audio_base64": audio_base64,
                    "audio_format": "audio/pcm",
                    "timestamp": dt.datetime.utcnow().isoformat(),
                },
                "request_id": request_id,
            },
        )

    async def _send_safely(self, websocket: WebSocket, data: dict) -> None:
        lock = self._get_send_lock(websocket)
        async with lock:
            try:
                if websocket.client_state.name == "CONNECTED" and websocket.application_state.name == "CONNECTED":
                    await websocket.send_text(json.dumps(data))
            except RuntimeError as e:
                # WebSocket already closed, ignore
                logger.debug(f"WebSocket send skipped (closed): {e}")
            except Exception as e:
                logger.warning(f"WebSocket send failed: {e}")

    def _get_send_lock(self, websocket: WebSocket) -> asyncio.Lock:
        lock = self._send_locks.get(websocket)
        if lock is None:
            lock = asyncio.Lock()
            self._send_locks[websocket] = lock
        return lock

    async def _handle_hardware_fire_alert(self, websocket: WebSocket, data: Dict[str, Any]) -> None:
        """
        Handle fire alerts from hardware flame sensor module (Raspberry Pi).

        Args:
            websocket: The WebSocket connection that sent the alert
            data: Alert data containing sensor_name, level, message, consecutive_count
        """
        sensor_name = data.get("sensor_name", "Unknown")
        level = data.get("level", "warning")
        message = data.get("message", "Phát hiện lửa từ cảm biến phần cứng")
        consecutive_count = data.get("consecutive_count", 0)
        timestamp = data.get("timestamp")

        logger.warning(
            "🔥 HARDWARE FIRE ALERT: sensor=%s, level=%s, count=%d, msg=%s",
            sensor_name, level, consecutive_count, message
        )

        # Generate voice notification for the fire alert
        audio_base64 = ""
        try:
            # Use cached fire alert audio if available, otherwise generate
            notification_text = f"Cảnh báo cháy! Cảm biến {sensor_name} phát hiện lửa. Mức độ {level}."
            audio_base64 = await self.notification_voice_service.generate_voice_notification_base64(
                notification_text
            )
        except Exception as exc:
            logger.error("Failed to generate fire alert voice notification: %s", exc)

        # Broadcast fire alert to all connected WebSocket clients
        # This will be forwarded to Android app and web frontend
        alert_payload = {
            "type": "fire_detection_alert",
            "source": "hardware_sensor",
            "sensor_name": sensor_name,
            "level": level,
            "message": message,
            "consecutive_count": consecutive_count,
            "timestamp": timestamp or dt.datetime.utcnow().isoformat(),
            "audio_base64": audio_base64,
        }

        await self._send_safely(websocket, alert_payload)
        logger.info("🔥 Hardware fire alert broadcast to client: %s", sensor_name)

        # Also notify through lighting service observer pattern for other connected clients
        try:
            # Use the lighting service's listener queue to broadcast to all clients
            # _listeners is a list of tuples: (event_loop, queue)
            for loop, listener_queue in self.smart_home_service.lighting_service._listeners:
                listener_queue.put_nowait({
                    "type": "hardware_fire_alert",
                    "sensor_name": sensor_name,
                    "level": level,
                    "message": message,
                    "consecutive_count": consecutive_count,
                    "timestamp": timestamp or dt.datetime.utcnow().isoformat(),
                })
        except Exception as exc:
            logger.error("Failed to broadcast fire alert to listeners: %s", exc)

    @staticmethod
    def _extract_sample_rate(mime_type: Optional[str]) -> Optional[int]:
        if not mime_type:
            return None
        for part in mime_type.split(";")[1:]:
            key, _, value = part.partition("=")
            if key.strip().lower() == "rate":
                try:
                    rate = int(value.strip())
                except ValueError:
                    return None
                return rate if rate > 0 else None
        return None
