"""
Flame Sensor Service cho Raspberry Pi
Polling cảm biến lửa và gửi cảnh báo khi phát hiện lửa

Module cảm biến lửa sử dụng:
- VCC: 3.3V-5V
- GND: GND
- DO: Digital Output (0 = có lửa, 1 = không có lửa)
- AO: Analog Output (không sử dụng trong phiên bản này)

Đặc điểm:
- Phát hiện ngọn lửa ở bước sóng 760nm-1100nm
- Khoảng cách phát hiện: ~80cm với bật lửa, xa hơn với ngọn lửa lớn
- Góc phát hiện: 60 độ
- Có potentiometer để điều chỉnh độ nhạy
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Callable, Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class FireAlertLevel(Enum):
    """Mức độ cảnh báo cháy"""
    NONE = "none"           # Không có lửa
    WARNING = "warning"     # Phát hiện lần đầu (có thể false positive)
    ALERT = "alert"         # Xác nhận có lửa (nhiều lần liên tiếp)
    CRITICAL = "critical"   # Cháy nghiêm trọng (phát hiện liên tục)


@dataclass
class FlameSensorConfig:
    """Cấu hình cho flame sensor service"""
    # Polling interval (giây)
    poll_interval: float = 0.1  # 100ms - đọc nhanh để phản hồi kịp thời

    # Debounce: số lần đọc liên tiếp để xác nhận có lửa
    # Giúp tránh false positive từ nhiễu
    confirm_readings: int = 3

    # Cooldown sau khi gửi alert (giây)
    # Tránh spam alerts
    alert_cooldown: float = 10.0

    # Thời gian tối đa giữa các lần phát hiện để được coi là liên tiếp
    consecutive_timeout: float = 1.0

    # Số lần phát hiện liên tiếp để nâng lên CRITICAL
    critical_threshold: int = 10


@dataclass
class FireDetectionResult:
    """Kết quả phát hiện lửa"""
    fire_detected: bool
    level: FireAlertLevel
    sensor_name: str
    consecutive_count: int
    last_detection_time: float
    message: str


class FlameSensorService:
    """
    Service polling cảm biến lửa

    Features:
    - Polling định kỳ với interval có thể cấu hình
    - Debouncing để tránh false positives
    - Cooldown để tránh spam alerts
    - Callback khi phát hiện lửa
    - Support nhiều sensors
    """

    def __init__(
        self,
        gpio_controller,  # GPIODevicesController
        config: FlameSensorConfig = None,
        mock_mode: bool = False
    ):
        """
        Args:
            gpio_controller: GPIODevicesController instance
            config: Cấu hình polling
            mock_mode: Chế độ mock (không cần hardware)
        """
        self.gpio = gpio_controller
        self.config = config or FlameSensorConfig()
        self.mock_mode = mock_mode

        # Tracking state for each sensor
        self._sensor_states: Dict[str, Dict[str, Any]] = {}

        # Callbacks
        self._fire_alert_callback: Optional[Callable[[FireDetectionResult], None]] = None

        # Running flag
        self.running = False
        self._poll_task: Optional[asyncio.Task] = None

    def set_fire_alert_callback(
        self,
        callback: Callable[[FireDetectionResult], None]
    ) -> None:
        """
        Đặt callback khi phát hiện lửa

        Args:
            callback: Function(FireDetectionResult) -> None
        """
        self._fire_alert_callback = callback

    def _init_sensor_state(self, sensor_name: str) -> Dict[str, Any]:
        """Khởi tạo state tracking cho một sensor"""
        return {
            "consecutive_fires": 0,      # Số lần phát hiện lửa liên tiếp
            "last_fire_time": 0.0,       # Thời gian phát hiện lửa gần nhất
            "last_alert_time": 0.0,      # Thời gian gửi alert gần nhất
            "current_level": FireAlertLevel.NONE,
            "reading_buffer": [],        # Buffer để debounce
        }

    def _get_sensor_state(self, sensor_name: str) -> Dict[str, Any]:
        """Lấy state của sensor, tạo mới nếu chưa có"""
        if sensor_name not in self._sensor_states:
            self._sensor_states[sensor_name] = self._init_sensor_state(sensor_name)
        return self._sensor_states[sensor_name]

    def _process_reading(
        self,
        sensor_name: str,
        fire_detected: bool
    ) -> Optional[FireDetectionResult]:
        """
        Xử lý một lần đọc sensor

        Returns:
            FireDetectionResult nếu cần gửi alert, None nếu không
        """
        state = self._get_sensor_state(sensor_name)
        current_time = time.time()

        # Thêm vào buffer để debounce
        state["reading_buffer"].append(fire_detected)

        # Giữ buffer size = confirm_readings
        if len(state["reading_buffer"]) > self.config.confirm_readings:
            state["reading_buffer"].pop(0)

        # Kiểm tra xem có đủ readings để confirm không
        if len(state["reading_buffer"]) < self.config.confirm_readings:
            return None

        # Xác nhận có lửa nếu tất cả readings gần đây đều True
        confirmed_fire = all(state["reading_buffer"])

        if confirmed_fire:
            # Kiểm tra có phải liên tiếp không
            time_since_last = current_time - state["last_fire_time"]

            if time_since_last <= self.config.consecutive_timeout:
                state["consecutive_fires"] += 1
            else:
                # Reset nếu đã quá lâu từ lần phát hiện trước
                state["consecutive_fires"] = 1

            state["last_fire_time"] = current_time

            # Xác định level
            if state["consecutive_fires"] >= self.config.critical_threshold:
                new_level = FireAlertLevel.CRITICAL
            elif state["consecutive_fires"] >= self.config.confirm_readings:
                new_level = FireAlertLevel.ALERT
            else:
                new_level = FireAlertLevel.WARNING

            # Kiểm tra cooldown
            time_since_alert = current_time - state["last_alert_time"]
            should_alert = (
                time_since_alert >= self.config.alert_cooldown or
                new_level.value > state["current_level"].value  # Nâng cấp level thì gửi ngay
            )

            if should_alert and new_level != FireAlertLevel.NONE:
                state["last_alert_time"] = current_time
                state["current_level"] = new_level

                # Tạo message
                if new_level == FireAlertLevel.CRITICAL:
                    message = f"🔥🔥🔥 CHÁY NGHIÊM TRỌNG! Cảm biến '{sensor_name}' phát hiện lửa liên tục!"
                elif new_level == FireAlertLevel.ALERT:
                    message = f"🔥 CẢNH BÁO CHÁY! Cảm biến '{sensor_name}' xác nhận có lửa!"
                else:
                    message = f"⚠️ Cảm biến '{sensor_name}' phát hiện có thể có lửa."

                return FireDetectionResult(
                    fire_detected=True,
                    level=new_level,
                    sensor_name=sensor_name,
                    consecutive_count=state["consecutive_fires"],
                    last_detection_time=current_time,
                    message=message,
                )
        else:
            # Không có lửa - reset state dần dần
            if state["consecutive_fires"] > 0:
                # Giảm dần để tránh nhảy level đột ngột
                state["consecutive_fires"] = max(0, state["consecutive_fires"] - 1)

            if state["consecutive_fires"] == 0:
                state["current_level"] = FireAlertLevel.NONE

        return None

    async def _poll_sensors(self) -> None:
        """Polling loop chính"""
        logger.info("Bắt đầu polling flame sensors...")

        while self.running:
            try:
                # Đọc tất cả flame sensors
                sensor_readings = self.gpio.get_all_flame_sensors()

                for sensor_name, fire_detected in sensor_readings.items():
                    result = self._process_reading(sensor_name, fire_detected)

                    if result and self._fire_alert_callback:
                        try:
                            self._fire_alert_callback(result)
                        except Exception as e:
                            logger.error(f"Lỗi trong fire alert callback: {e}")

                await asyncio.sleep(self.config.poll_interval)

            except asyncio.CancelledError:
                logger.info("Flame sensor polling bị hủy")
                break
            except Exception as e:
                logger.error(f"Lỗi khi polling flame sensor: {e}")
                await asyncio.sleep(1.0)  # Wait longer on error

    def start(self) -> None:
        """Bắt đầu polling service"""
        if self.running:
            logger.warning("Flame sensor service đã đang chạy")
            return

        self.running = True
        self._poll_task = asyncio.create_task(self._poll_sensors())
        logger.info("Flame sensor service đã bắt đầu")

    async def stop(self) -> None:
        """Dừng polling service"""
        if not self.running:
            return

        self.running = False

        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None

        logger.info("Flame sensor service đã dừng")

    def get_status(self) -> Dict[str, Any]:
        """Lấy trạng thái hiện tại của tất cả sensors"""
        status = {}
        for sensor_name, state in self._sensor_states.items():
            status[sensor_name] = {
                "level": state["current_level"].value,
                "consecutive_fires": state["consecutive_fires"],
                "last_fire_time": state["last_fire_time"],
                "last_alert_time": state["last_alert_time"],
            }
        return status

    def trigger_test_alert(self, sensor_name: str = "Test Sensor") -> None:
        """
        Trigger một test alert (cho testing)

        Args:
            sensor_name: Tên sensor giả để test
        """
        if self._fire_alert_callback:
            result = FireDetectionResult(
                fire_detected=True,
                level=FireAlertLevel.ALERT,
                sensor_name=sensor_name,
                consecutive_count=5,
                last_detection_time=time.time(),
                message=f"🔥 [TEST] Cảnh báo cháy thử nghiệm từ '{sensor_name}'",
            )
            self._fire_alert_callback(result)
            logger.info(f"Đã trigger test alert cho '{sensor_name}'")
