"""
IoT Client chính cho Raspberry Pi 5
Điều phối tất cả services: GPIO, Camera, Audio, WebSocket
"""

import asyncio
import logging
import signal
import sys
from typing import Dict

from gpio_devices import GPIODevicesController, GPIODeviceConfig, DeviceType
from camera_service import CameraService, CameraConfig
from audio_handler import AudioHandler, AudioConfig
from websocket_client import WebSocketClient, WebSocketConfig


logger = logging.getLogger(__name__)


class IoTClient:
    """
    Main IoT Client orchestrator

    Quản lý và điều phối:
    - GPIO Controller (relay module)
    - Camera Service (USB webcam)
    - Audio Handler (microphone + speaker)
    - WebSocket Client (kết nối backend)
    """

    def __init__(
        self,
        gpio_configs: Dict[str, GPIODeviceConfig],
        camera_config: CameraConfig,
        audio_config: AudioConfig,
        websocket_config: WebSocketConfig,
        mock_mode: bool = False
    ):
        """
        Args:
            gpio_configs: Dict của GPIO device configs
            camera_config: Camera configuration
            audio_config: Audio configuration
            websocket_config: WebSocket configuration
            mock_mode: Chạy ở chế độ mock (không dùng hardware)
        """
        self.mock_mode = mock_mode

        # Initialize components
        self.gpio = GPIODevicesController(gpio_configs, mock_mode=mock_mode)
        self.camera = CameraService(camera_config, mock_mode=mock_mode)
        self.audio = AudioHandler(audio_config, mock_mode=mock_mode)
        self.websocket = WebSocketClient(websocket_config)

        # Setup callbacks
        self._setup_callbacks()

        # Running flag
        self.running = False

    def _setup_callbacks(self) -> None:
        """Setup callbacks giữa các components"""

        # Camera frame → WebSocket
        def on_camera_frame(jpeg_b64: str):
            """Callback khi có frame mới từ camera"""
            if self.websocket.connected:
                asyncio.create_task(self.websocket.send_camera_frame(jpeg_b64))

        self.camera.set_frame_callback(on_camera_frame)

        # Microphone audio → WebSocket
        def on_audio_chunk(audio_b64: str):
            """Callback khi có audio chunk từ microphone"""
            if self.websocket.connected:
                asyncio.create_task(
                    self.websocket.send_audio_chunk(audio_b64, self.audio.config.sample_rate)
                )

        self.audio.set_audio_callback(on_audio_chunk)

        # WebSocket light/device update → GPIO
        def on_light_update(location: str, is_on: bool):
            """Callback khi nhận lệnh cập nhật đèn/device từ server"""
            logger.info(f"Nhận lệnh: {'Bật' if is_on else 'Tắt'} '{location}'")

            # Tự động phát hiện device type và điều khiển
            device_key = location.lower().strip()

            # Thử các loại device
            if is_on:
                # Try LED first
                if self.gpio.led_on(location):
                    return
                # Try relay
                if self.gpio.relay_on(location):
                    return
                # Try buzzer
                if self.gpio.buzzer_on(location):
                    return
            else:
                if self.gpio.led_off(location):
                    return
                if self.gpio.relay_off(location):
                    return
                if self.gpio.buzzer_off(location):
                    return

        self.websocket.set_light_update_callback(on_light_update)

        # WebSocket audio response → Speaker
        def on_audio_response(audio_b64: str, sample_rate: int):
            """Callback khi nhận audio response từ server"""
            self.audio.play_audio_chunk(audio_b64, sample_rate)

        self.websocket.set_audio_response_callback(on_audio_response)

        # WebSocket fire alert → Speaker
        def on_fire_alert(message: str, audio_b64: str):
            """Callback khi nhận cảnh báo cháy"""
            logger.warning(f"🔥 CẢNH BÁO CHÁY: {message}")
            if audio_b64:
                # Phát âm thanh cảnh báo
                self.audio.play_audio_chunk(audio_b64, 24000)

        self.websocket.set_fire_alert_callback(on_fire_alert)

        # WebSocket general message → Log
        def on_message(message: dict):
            """Callback cho tất cả messages"""
            # Log message (có thể thêm xử lý khác nếu cần)
            pass

        self.websocket.set_message_callback(on_message)

    async def initialize(self) -> bool:
        """
        Khởi tạo tất cả components

        Returns:
            True nếu thành công
        """
        logger.info("=== Khởi tạo IoT Client ===")

        # Initialize GPIO
        logger.info("Khởi tạo GPIO controller...")
        # GPIO đã được init trong __init__

        # Initialize Camera
        logger.info("Khởi tạo camera...")
        if not self.camera.initialize():
            logger.error("❌ Không thể khởi tạo camera")
            return False

        # Initialize Audio
        logger.info("Khởi tạo audio...")
        if not self.audio.initialize():
            logger.error("❌ Không thể khởi tạo audio")
            return False

        logger.info("✓ Tất cả components đã được khởi tạo")
        return True

    async def start(self) -> None:
        """Bắt đầu tất cả services"""
        logger.info("=== Bắt đầu IoT Client ===")

        # Start camera capture
        logger.info("Bắt đầu camera capture...")
        self.camera.start_capture()

        # Start audio recording và playback
        logger.info("Bắt đầu audio recording...")
        self.audio.start_recording()

        logger.info("Bắt đầu audio playback...")
        self.audio.start_playback()

        # Start WebSocket client
        logger.info("Bắt đầu WebSocket client...")
        self.running = True

        # Run WebSocket (sẽ auto-reconnect)
        await self.websocket.run()

    async def stop(self) -> None:
        """Dừng tất cả services"""
        logger.info("=== Dừng IoT Client ===")

        self.running = False

        # Stop WebSocket
        self.websocket.stop()
        await self.websocket.disconnect()

        # Stop camera
        self.camera.stop_capture()

        # Stop audio
        self.audio.stop_recording()
        self.audio.stop_playback()

        logger.info("✓ Tất cả services đã dừng")

    def cleanup(self) -> None:
        """Cleanup tất cả resources"""
        logger.info("=== Cleanup IoT Client ===")

        self.camera.cleanup()
        self.audio.cleanup()
        self.gpio.cleanup()

        logger.info("✓ Cleanup hoàn tất")


async def main():
    """Main entry point"""

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/var/log/iot-client.log')
        ]
    )

    logger.info("=" * 50)
    logger.info("IoT Smart Home Client - Raspberry Pi 5")
    logger.info("=" * 50)

    # Load config (có thể load từ file .env hoặc config.json)
    # Ví dụ đơn giản:

    # GPIO configs - Cấu hình các thiết bị GPIO
    # Thay đổi theo thiết bị thực tế của bạn!
    gpio_configs = {
        # LEDs
        "LED Đỏ": GPIODeviceConfig(
            gpio_pin=17,
            name="LED Đỏ",
            device_type=DeviceType.LED,
            active_high=True
        ),
        "LED Xanh": GPIODeviceConfig(
            gpio_pin=27,
            name="LED Xanh",
            device_type=DeviceType.LED,
            active_high=True
        ),
        "LED Vàng": GPIODeviceConfig(
            gpio_pin=22,
            name="LED Vàng",
            device_type=DeviceType.LED,
            active_high=True
        ),
        # Buzzer
        "Buzzer": GPIODeviceConfig(
            gpio_pin=23,
            name="Buzzer Cảnh báo",
            device_type=DeviceType.BUZZER,
            active_high=True
        ),
        # Servo (nếu có)
        "Servo Cửa": GPIODeviceConfig(
            gpio_pin=18,  # GPIO 18 hỗ trợ hardware PWM
            name="Servo Cửa",
            device_type=DeviceType.SERVO,
        ),

        # Comment out các devices bạn chưa có:
        # "Relay 1": GPIODeviceConfig(
        #     gpio_pin=24,
        #     name="Relay Đèn",
        #     device_type=DeviceType.RELAY,
        #     active_high=False  # Relay thường active LOW
        # ),
    }

    # Camera config
    camera_config = CameraConfig(
        device_index=0,  # /dev/video0
        width=1280,
        height=720,
        fps=30,
        capture_interval=0.5,
        jpeg_quality=75,
        max_dimension=720
    )

    # Audio config
    audio_config = AudioConfig(
        sample_rate=16000,
        channels=1,
        chunk_size=1600,
    )

    # WebSocket config
    websocket_config = WebSocketConfig(
        server_url="ws://localhost:8000/ws/gemini",  # Thay bằng IP backend
        reconnect_delay=3.0,
        ping_interval=10.0,
    )

    # Mock mode để test (không cần hardware thật)
    # Set MOCK_MODE=true trong environment để enable
    import os
    mock_mode = os.getenv("MOCK_MODE", "false").lower() in ("true", "1", "yes")

    # Create client
    client = IoTClient(
        gpio_configs=gpio_configs,
        camera_config=camera_config,
        audio_config=audio_config,
        websocket_config=websocket_config,
        mock_mode=mock_mode
    )

    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info(f"Nhận signal {sig}, đang dừng...")
        asyncio.create_task(client.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize
    if not await client.initialize():
        logger.error("Không thể khởi tạo IoT Client")
        sys.exit(1)

    # Start
    try:
        await client.start()
    except Exception as e:
        logger.error(f"Lỗi khi chạy IoT Client: {e}", exc_info=True)
    finally:
        # Cleanup
        client.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("IoT Client đã dừng bởi người dùng")
    except Exception as e:
        logger.error(f"Lỗi nghiêm trọng: {e}", exc_info=True)
        sys.exit(1)
