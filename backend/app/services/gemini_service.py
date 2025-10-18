"""Gemini Live WebSocket service tailored for the smart home assistant."""

from __future__ import annotations

import asyncio
import base64
import binascii
import datetime as dt
import json
import logging
from pathlib import Path
from typing import Dict, Optional

from fastapi import WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types

from app.core.config import settings
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

    Quy tắc sử dụng tool:
    1. Nếu người dùng nhắc đến bật đèn, chiếu sáng, sáng đèn,... hãy gọi tool turn_on_light.
    2. Nếu người dùng nhắc đến tắt đèn, dập đèn,... hãy gọi tool turn_off_light.
    3. Nếu người dùng muốn nghe nhạc, hãy gọi tool play_music và truyền tên bài hát họ nêu ra.

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

        self.conversation_history_file: Path = history_file or settings.conversation_history_file
        self.conversation_history_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.conversation_history_file.exists():
            self.conversation_history_file.write_text("[]", encoding="utf-8")

        self._current_user_input = ""
        self._current_assistant_output = ""
        self._send_locks: Dict[WebSocket, asyncio.Lock] = {}
        self._default_output_sample_rate = 24000

    # ------------------------------------------------------------------
    # WebSocket orchestration
    # ------------------------------------------------------------------
    async def handle_websocket_connection(self, websocket: WebSocket) -> None:
        """Main entry point for the Gemini WebSocket connection."""

        previous_session_handle = self.session_service.load_previous_session_handle()
        await self._send_safely(websocket, {"setupComplete": {}})

        if not self.client:
            logger.warning("Google API key is missing. Running in offline echo mode.")
            await self._run_offline_loop(websocket)
            return

        config = self._create_live_config(previous_session_handle)

        send_task = receive_task = ping_task = None
        try:
            async with self.client.aio.live.connect(model=self.model, config=config) as session:
                send_task = asyncio.create_task(
                    self._relay_client_to_gemini(websocket, session)
                )
                receive_task = asyncio.create_task(
                    self._relay_gemini_to_client(websocket, session)
                )
                ping_task = asyncio.create_task(self._ping_websocket(websocket))

                done, pending = await asyncio.wait(
                    [send_task, receive_task, ping_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
                for task in done:
                    task.result()
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected by client")
        finally:
            for task in filter(None, [send_task, receive_task, ping_task]):
                if not task.done():
                    task.cancel()
            self._send_locks.pop(websocket, None)

    async def _run_offline_loop(self, websocket: WebSocket) -> None:
        """Fallback mode used during tests when Gemini credentials are absent."""

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

    # ------------------------------------------------------------------
    # Gemini streaming relays
    # ------------------------------------------------------------------
    async def _relay_client_to_gemini(self, websocket: WebSocket, session) -> None:
        try:
            logger.info("🚀 Client -> Gemini relay started")
            while True:
                message = await asyncio.wait_for(
                    websocket.receive_text(), timeout=settings.websocket_receive_timeout
                )
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
                    for chunk in data["realtime_input"].get("media_chunks", []):
                        mime = chunk.get("mime_type", "")
                        payload = chunk.get("data")
                        if not payload:
                            continue

                        payload_bytes: Optional[bytes]
                        if isinstance(payload, str):
                            try:
                                payload_bytes = base64.b64decode(payload)
                            except (ValueError, binascii.Error):
                                logger.warning("Không thể giải mã dữ liệu realtime_input")
                                payload_bytes = None
                        elif isinstance(payload, (bytes, bytearray)):
                            payload_bytes = bytes(payload)
                        else:
                            payload_bytes = None

                        if not payload_bytes:
                            continue

                        blob = types.Blob(data=payload_bytes, mime_type=mime)
                        await session.send_realtime_input(
                            audio=blob if mime.startswith("audio/") else None,
                            media=blob if mime.startswith("image/") else None,
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
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for client message")
        except WebSocketDisconnect:
            logger.info("Client disconnected (send loop)")
        finally:
            logger.info("Client -> Gemini relay stopped")

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
                            if update.resumable and update.new_handle:
                                self.session_service.save_previous_session_handle(update.new_handle)

                        if response.server_content and response.server_content.turn_complete:
                            logger.info("\n<Turn complete>")
                            logger.info("=" * 50)
                            logger.info("🎯 Turn hoàn thành, sẵn sàng nhận input tiếp theo")
                            
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
                if matched:
                    payload = {
                        "result": "success",
                        "requested_title": title,
                        "matched_song": matched,
                    }
                    await self._send_safely(
                        websocket,
                        {
                            "type": "smart_home_music",
                            "requested_title": title,
                            "matched_song": matched,
                        },
                    )
                else:
                    payload = {
                        "result": "not_found",
                        "requested_title": title,
                    }
                    await self._send_safely(
                        websocket,
                        {
                            "type": "smart_home_music",
                            "requested_title": title,
                            "matched_song": None,
                        },
                    )
                responses.append(
                    types.FunctionResponse(
                        id=function_call.id,
                        name=name,
                        response=payload,
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
        session_resumption_cfg = None
        if previous_session_handle:
            session_resumption_cfg = types.SessionResumptionConfig(handle=previous_session_handle)

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
            if websocket.client_state.name == "CONNECTED":
                await websocket.send_text(json.dumps(data))

    def _get_send_lock(self, websocket: WebSocket) -> asyncio.Lock:
        lock = self._send_locks.get(websocket)
        if lock is None:
            lock = asyncio.Lock()
            self._send_locks[websocket] = lock
        return lock

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
