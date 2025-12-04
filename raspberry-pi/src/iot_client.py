"""
IoT Client chính cho Raspberry Pi 5
Điều phối tất cả services: GPIO, Camera, Audio, WebSocket
"""

import asyncio
import logging
import os
import signal
import sys
from typing import Dict, Optional

from gpio_devices import GPIODevicesController, GPIODeviceConfig, DeviceType
from camera_service import CameraService, CameraConfig
from audio_handler import AudioHandler, AudioConfig
from websocket_client import WebSocketClient, WebSocketConfig
from flame_sensor_service import FlameSensorService, FlameSensorConfig, FireDetectionResult


logger = logging.getLogger(__name__)


class IoTClient:
    """
    Main IoT Client orchestrator

    Quản lý và điều phối:
    - GPIO Controller (relay module)
    - Camera Service (USB webcam)
    - Audio Handler (microphone + speaker)
    - WebSocket Client (kết nối backend)
    - Flame Sensor Service (cảm biến lửa phần cứng)
    """

    def __init__(
        self,
        gpio_configs: Dict[str, GPIODeviceConfig],
        camera_config: CameraConfig,
        audio_config: AudioConfig,
        websocket_config: WebSocketConfig,
        flame_sensor_config: Optional[FlameSensorConfig] = None,
        mock_mode: bool = False
    ):
        """
        Args:
            gpio_configs: Dict của GPIO device configs
            camera_config: Camera configuration
            audio_config: Audio configuration
            websocket_config: WebSocket configuration
            flame_sensor_config: Flame sensor configuration (optional)
            mock_mode: Chạy ở chế độ mock (không dùng hardware)
        """
        self.mock_mode = mock_mode
        self.loop: Optional[asyncio.AbstractEventLoop] = None

        # Initialize components
        self.gpio = GPIODevicesController(gpio_configs, mock_mode=mock_mode)
        self.camera = CameraService(camera_config, mock_mode=mock_mode)
        self.audio = AudioHandler(audio_config, mock_mode=mock_mode)
        self.websocket = WebSocketClient(websocket_config)

        # Initialize flame sensor service if there are flame sensors configured
        has_flame_sensors = any(
            cfg.device_type == DeviceType.FLAME_SENSOR
            for cfg in gpio_configs.values()
        )
        if has_flame_sensors:
            self.flame_sensor = FlameSensorService(
                gpio_controller=self.gpio,
                config=flame_sensor_config or FlameSensorConfig(),
                mock_mode=mock_mode
            )
            logger.info("Flame sensor service initialized")
        else:
            self.flame_sensor = None
            logger.info("No flame sensors configured")

        # Setup callbacks
        self._setup_callbacks()

        # Running flag
        self.running = False

    def _setup_callbacks(self) -> None:
        """Setup callbacks giữa các components"""

        # Camera frame → WebSocket
        def on_camera_frame(jpeg_b64: str):
            """Callback khi có frame mới từ camera"""
            if self.websocket.connected and self.loop is not None:
                # Schedule coroutine from sync thread using thread-safe method
                asyncio.run_coroutine_threadsafe(
                    self.websocket.send_camera_frame(jpeg_b64),
                    self.loop
                )

        self.camera.set_frame_callback(on_camera_frame)

        # Microphone audio → WebSocket
        def on_audio_chunk(audio_b64: str):
            """Callback khi có audio chunk từ microphone"""
            if self.websocket.connected and self.loop is not None:
                # Schedule coroutine from sync thread using thread-safe method
                asyncio.run_coroutine_threadsafe(
                    self.websocket.send_audio_chunk(audio_b64, self.audio.config.sample_rate),
                    self.loop
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

        # WebSocket fire alert → Speaker + Buzzer
        def on_fire_alert(message: str, audio_b64: str):
            """Callback khi nhận cảnh báo cháy"""
            logger.warning(f"🔥 CẢNH BÁO CHÁY: {message}")

            # Kích hoạt buzzer - beep 5 lần nhanh
            self.gpio.buzzer_beep("Buzzer", on_time=0.2, off_time=0.1, n=150)

            if audio_b64:
                # Phát âm thanh cảnh báo qua speaker
                self.audio.play_audio_chunk(audio_b64, 24000)

        self.websocket.set_fire_alert_callback(on_fire_alert)

        # WebSocket motor control → GPIO Motor
        def on_motor_control(name: str, action: str, speed: float):
            """Callback khi nhận lệnh điều khiển motor từ server"""
            logger.info(f"Nhận lệnh motor: '{name}' → {action} (tốc độ {speed*100:.0f}%)")

            if action in ("on", "forward"):
                self.gpio.motor_forward(name, speed)
            elif action in ("backward", "reverse"):
                self.gpio.motor_backward(name, speed)
            elif action in ("off", "stop"):
                self.gpio.motor_stop(name)
            else:
                logger.warning(f"Hành động motor không hợp lệ: {action}")

        self.websocket.set_motor_control_callback(on_motor_control)

        # WebSocket door control → GPIO Servo
        def on_door_control(name: str, action: str, angle: float):
            """Callback khi nhận lệnh điều khiển cửa từ server"""
            logger.info(f"Nhận lệnh cửa: '{name}' → {action} (góc {angle}°)")

            if action == "open":
                # Mở cửa = xoay servo về 0° (servo mounted in reverse)
                self.gpio.servo_set_angle(name, 0)
                logger.info(f"🚪 Đã mở cửa '{name}'")
            elif action == "close":
                # Đóng cửa = xoay servo đến 90°
                self.gpio.servo_set_angle(name, 90)
                logger.info(f"🚪 Đã đóng cửa '{name}'")
            elif action == "set_angle":
                # Đặt góc tùy chỉnh
                self.gpio.servo_set_angle(name, angle)
            else:
                logger.warning(f"Hành động cửa không hợp lệ: {action}")

        self.websocket.set_door_control_callback(on_door_control)

        # WebSocket general message → Log
        def on_message(message: dict):
            """Callback cho tất cả messages"""
            # Log message (có thể thêm xử lý khác nếu cần)
            pass

        self.websocket.set_message_callback(on_message)

        # Flame sensor alert → WebSocket + Buzzer
        if self.flame_sensor:
            def on_hardware_fire_alert(result: FireDetectionResult):
                """Callback khi flame sensor phát hiện lửa"""
                logger.warning(f"🔥 FLAME SENSOR ALERT: {result.message}")

                # Kích hoạt buzzer dựa trên mức độ
                if result.level.value == "critical":
                    # Beep liên tục cho critical
                    self.gpio.buzzer_beep("Buzzer", on_time=0.1, off_time=0.05, n=200)
                elif result.level.value == "alert":
                    # Beep nhanh cho alert
                    self.gpio.buzzer_beep("Buzzer", on_time=0.2, off_time=0.1, n=100)
                elif result.level.value == "warning":
                    # Beep chậm cho warning
                    self.gpio.buzzer_beep("Buzzer", on_time=0.3, off_time=0.2, n=5)

                # Gửi alert tới backend
                if self.websocket.connected and self.loop is not None:
                    asyncio.run_coroutine_threadsafe(
                        self.websocket.send_hardware_fire_alert(
                            sensor_name=result.sensor_name,
                            level=result.level.value,
                            message=result.message,
                            consecutive_count=result.consecutive_count
                        ),
                        self.loop
                    )

            self.flame_sensor.set_fire_alert_callback(on_hardware_fire_alert)

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

        # Lưu event loop để dùng trong callbacks
        self.loop = asyncio.get_event_loop()

        # Start camera capture
        logger.info("Bắt đầu camera capture...")
        self.camera.start_capture()

        # Start audio recording và playback
        logger.info("Bắt đầu audio recording...")
        self.audio.start_recording()

        logger.info("Bắt đầu audio playback...")
        self.audio.start_playback()

        # Start flame sensor service
        if self.flame_sensor:
            logger.info("Bắt đầu flame sensor service...")
            self.flame_sensor.start()

        # Start WebSocket client
        logger.info("Bắt đầu WebSocket client...")
        self.running = True

        # Run WebSocket (sẽ auto-reconnect)
        await self.websocket.run()

    async def stop(self) -> None:
        """Dừng tất cả services"""
        logger.info("=== Dừng IoT Client ===")

        self.running = False

        # Stop flame sensor
        if self.flame_sensor:
            await self.flame_sensor.stop()

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
        # LEDs - Mapped to rooms
        "Phòng khách": GPIODeviceConfig(
            gpio_pin=17,
            name="Phòng khách",
            device_type=DeviceType.LED,
            active_high=True
        ),
        "Phòng ngủ": GPIODeviceConfig(
            gpio_pin=27,
            name="Phòng ngủ",
            device_type=DeviceType.LED,
            active_high=True
        ),
        "Nhà bếp": GPIODeviceConfig(
            gpio_pin=22,
            name="Nhà bếp",
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
        # DC Motor (Quạt) - L298N driver
        "Quạt": GPIODeviceConfig(
            gpio_pin=(16, 20, 18),  # (IN1=GPIO16, IN2=GPIO20, ENA=GPIO18)
            name="Quạt",
            device_type=DeviceType.MOTOR,
        ),

        # Flame Sensor (Cảm biến lửa) - Module phát hiện lửa
        # Kết nối: DO → GPIO24 (hoặc GPIO khác còn trống)
        "Cảm biến lửa": GPIODeviceConfig(
            gpio_pin=24,  # GPIO24 cho DO (Digital Output)
            name="Cảm biến lửa",
            device_type=DeviceType.FLAME_SENSOR,
            # active_high=False vì sensor output LOW khi có lửa
        ),

        # Door Servo (Servo cửa) - SG90 hoặc MG90S
        # Kết nối: Signal → GPIO25, VCC → 5V, GND → GND
        # 0° = đóng cửa, 90° = mở cửa
        "Cửa chính": GPIODeviceConfig(
            gpio_pin=25,  # GPIO25 cho Signal
            name="Cửa chính",
            device_type=DeviceType.SERVO,
            min_pulse_width=0.5/1000,   # 0.5ms cho SG90
            max_pulse_width=2.5/1000,   # 2.5ms cho SG90
            frame_width=20.0/1000,      # 20ms (50Hz)
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
    websocket_url = os.getenv("WEBSOCKET_SERVER_URL", "ws://localhost:8000/ws/gemini")
    websocket_config = WebSocketConfig(
        server_url=websocket_url,
        reconnect_delay=3.0,
        ping_interval=10.0,
    )

    # Flame sensor config
    flame_sensor_config = FlameSensorConfig(
        poll_interval=0.1,       # 100ms - đọc nhanh
        confirm_readings=3,       # 3 lần liên tiếp để xác nhận
        alert_cooldown=10.0,      # 10s giữa các alerts
        critical_threshold=10,    # 10 lần để nâng lên critical
    )

    # Mock mode để test (không cần hardware thật)
    # Set MOCK_MODE=true trong environment để enable
    mock_mode = os.getenv("MOCK_MODE", "false").lower() in ("true", "1", "yes")

    # Create client
    client = IoTClient(
        gpio_configs=gpio_configs,
        camera_config=camera_config,
        audio_config=audio_config,
        websocket_config=websocket_config,
        flame_sensor_config=flame_sensor_config,
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
