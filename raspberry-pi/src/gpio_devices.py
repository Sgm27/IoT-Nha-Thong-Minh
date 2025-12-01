"""
GPIO Devices Controller cho Raspberry Pi 5
Support nhiều loại devices: LED, Buzzer, Servo, Relay
"""

import logging
from typing import Dict, Optional, Union
from dataclasses import dataclass
from enum import Enum

try:
    from gpiozero import OutputDevice, LED, Buzzer, Servo, PWMOutputDevice, Motor
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("gpiozero không khả dụng - chạy ở chế độ mock")


logger = logging.getLogger(__name__)


class DeviceType(Enum):
    """Loại thiết bị GPIO"""
    LED = "led"
    BUZZER = "buzzer"
    SERVO = "servo"
    RELAY = "relay"
    PWM = "pwm"
    MOTOR = "motor"


@dataclass
class GPIODeviceConfig:
    """Cấu hình cho một GPIO device"""
    gpio_pin: Union[int, tuple]  # int for single pin, tuple (forward, backward, enable) for motor
    name: str
    device_type: DeviceType
    active_high: bool = True  # LED, Buzzer thường active HIGH, Relay thường active LOW

    # Servo specific
    min_pulse_width: float = 1.0/1000  # 1ms
    max_pulse_width: float = 2.0/1000  # 2ms
    frame_width: float = 20.0/1000     # 20ms (50Hz)

    # PWM specific
    frequency: int = 1000  # Hz

    # Motor specific (for L298N driver)
    # gpio_pin should be tuple: (forward_pin, backward_pin, enable_pin)


class GPIODevicesController:
    """
    Controller cho tất cả GPIO devices

    Support:
    - LED: Bật/tắt đơn giản
    - Buzzer: Bật/tắt âm thanh
    - Servo: Điều khiển góc quay (0-180 độ)
    - Relay: Bật/tắt relay (active LOW/HIGH)
    - PWM: PWM output với tần số tùy chỉnh
    """

    def __init__(self, device_configs: Dict[str, GPIODeviceConfig], mock_mode: bool = False):
        """
        Args:
            device_configs: Dict mapping device name -> GPIODeviceConfig
            mock_mode: Nếu True, không điều khiển GPIO thực (để test)
        """
        self.device_configs = device_configs
        self.mock_mode = mock_mode or not GPIO_AVAILABLE
        self.devices: Dict[str, Union[LED, Buzzer, Servo, OutputDevice, PWMOutputDevice, None]] = {}
        self._states: Dict[str, Union[bool, float]] = {}

        self._initialize_devices()

    def _initialize_devices(self) -> None:
        """Khởi tạo tất cả GPIO devices"""
        for name, config in self.device_configs.items():
            device_key = name.lower().strip()

            if self.mock_mode:
                logger.info(
                    f"[MOCK] Khởi tạo {config.device_type.value} '{config.name}' "
                    f"(GPIO{config.gpio_pin})"
                )
                self.devices[device_key] = None
                self._states[device_key] = 0 if config.device_type == DeviceType.SERVO else False
            else:
                try:
                    device = self._create_device(config)
                    self.devices[device_key] = device
                    self._states[device_key] = 0 if config.device_type == DeviceType.SERVO else False
                    logger.info(
                        f"Khởi tạo {config.device_type.value} '{config.name}' tại GPIO{config.gpio_pin}"
                    )
                except Exception as e:
                    logger.error(f"Lỗi khởi tạo GPIO{config.gpio_pin} cho '{config.name}': {e}")
                    self.devices[device_key] = None
                    self._states[device_key] = 0 if config.device_type == DeviceType.SERVO else False

    def _create_device(self, config: GPIODeviceConfig):
        """Tạo GPIO device dựa trên type"""
        if config.device_type == DeviceType.LED:
            return LED(config.gpio_pin, active_high=config.active_high, initial_value=False)

        elif config.device_type == DeviceType.BUZZER:
            return Buzzer(config.gpio_pin, active_high=config.active_high, initial_value=False)

        elif config.device_type == DeviceType.SERVO:
            return Servo(
                config.gpio_pin,
                min_pulse_width=config.min_pulse_width,
                max_pulse_width=config.max_pulse_width,
                frame_width=config.frame_width
            )

        elif config.device_type == DeviceType.RELAY:
            return OutputDevice(config.gpio_pin, active_high=config.active_high, initial_value=False)

        elif config.device_type == DeviceType.PWM:
            return PWMOutputDevice(config.gpio_pin, frequency=config.frequency, initial_value=0)

        elif config.device_type == DeviceType.MOTOR:
            # Motor requires 3 pins: (forward, backward, enable)
            if isinstance(config.gpio_pin, tuple) and len(config.gpio_pin) == 3:
                forward_pin, backward_pin, enable_pin = config.gpio_pin
                return Motor(
                    forward=forward_pin,
                    backward=backward_pin,
                    enable=enable_pin
                )
            else:
                logger.error(f"Motor '{config.name}' cần 3 pins (forward, backward, enable)")
                return None

        else:
            # Default: OutputDevice
            return OutputDevice(config.gpio_pin, active_high=config.active_high, initial_value=False)

    # ===== LED Methods =====

    def led_on(self, name: str) -> bool:
        """Bật LED"""
        return self._turn_on(name, DeviceType.LED)

    def led_off(self, name: str) -> bool:
        """Tắt LED"""
        return self._turn_off(name, DeviceType.LED)

    def led_toggle(self, name: str) -> bool:
        """Toggle LED"""
        device_key = name.lower().strip()
        current_state = self._states.get(device_key, False)
        return self.led_off(name) if current_state else self.led_on(name)

    # ===== Buzzer Methods =====

    def buzzer_on(self, name: str) -> bool:
        """Bật buzzer"""
        return self._turn_on(name, DeviceType.BUZZER)

    def buzzer_off(self, name: str) -> bool:
        """Tắt buzzer"""
        return self._turn_off(name, DeviceType.BUZZER)

    def buzzer_beep(self, name: str, on_time: float = 0.1, off_time: float = 0.1, n: int = 1) -> bool:
        """
        Beep buzzer n lần

        Args:
            name: Device name
            on_time: Thời gian bật (giây)
            off_time: Thời gian tắt (giây)
            n: Số lần beep
        """
        device_key = name.lower().strip()

        if device_key not in self.devices:
            logger.warning(f"Không tìm thấy buzzer: '{name}'")
            return False

        if self.mock_mode:
            logger.info(f"[MOCK] Buzzer '{name}' beep {n} lần")
            return True

        device = self.devices[device_key]
        if device is None or not isinstance(device, Buzzer):
            return False

        try:
            device.beep(on_time=on_time, off_time=off_time, n=n, background=True)
            logger.info(f"Buzzer '{name}' beep {n} lần")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi beep buzzer '{name}': {e}")
            return False

    # ===== Servo Methods =====

    def servo_set_angle(self, name: str, angle: float) -> bool:
        """
        Đặt góc servo (0-180 độ)

        Args:
            name: Device name
            angle: Góc từ 0-180 độ
        """
        device_key = name.lower().strip()

        if device_key not in self.devices:
            logger.warning(f"Không tìm thấy servo: '{name}'")
            return False

        # Clamp angle 0-180
        angle = max(0, min(180, angle))

        if self.mock_mode:
            logger.info(f"[MOCK] Servo '{name}' -> {angle}°")
            self._states[device_key] = angle
            return True

        device = self.devices[device_key]
        if device is None or not isinstance(device, Servo):
            return False

        try:
            # Convert angle (0-180) to servo value (-1 to 1)
            # 0° = -1, 90° = 0, 180° = 1
            servo_value = (angle - 90) / 90
            device.value = servo_value
            self._states[device_key] = angle
            logger.info(f"Servo '{name}' -> {angle}°")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi điều khiển servo '{name}': {e}")
            return False

    def servo_center(self, name: str) -> bool:
        """Đặt servo về giữa (90°)"""
        return self.servo_set_angle(name, 90)

    def servo_min(self, name: str) -> bool:
        """Đặt servo về min (0°)"""
        return self.servo_set_angle(name, 0)

    def servo_max(self, name: str) -> bool:
        """Đặt servo về max (180°)"""
        return self.servo_set_angle(name, 180)

    # ===== Relay Methods =====

    def relay_on(self, name: str) -> bool:
        """Bật relay"""
        return self._turn_on(name, DeviceType.RELAY)

    def relay_off(self, name: str) -> bool:
        """Tắt relay"""
        return self._turn_off(name, DeviceType.RELAY)

    # ===== Motor Methods =====

    def motor_forward(self, name: str, speed: float = 1.0) -> bool:
        """
        Chạy motor tiến

        Args:
            name: Device name
            speed: Tốc độ từ 0.0 - 1.0 (0% - 100%)
        """
        device_key = name.lower().strip()

        if device_key not in self.devices:
            logger.warning(f"Không tìm thấy motor: '{name}'")
            return False

        # Clamp speed 0-1
        speed = max(0.0, min(1.0, speed))

        if self.mock_mode:
            logger.info(f"[MOCK] Motor '{name}' chạy tiến {speed*100:.0f}%")
            self._states[device_key] = ("forward", speed)
            return True

        device = self.devices[device_key]
        if device is None or not isinstance(device, Motor):
            logger.warning(f"Device '{name}' không phải motor")
            return False

        try:
            device.forward(speed=speed)
            self._states[device_key] = ("forward", speed)
            logger.info(f"Motor '{name}' chạy tiến {speed*100:.0f}%")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi điều khiển motor '{name}': {e}")
            return False

    def motor_backward(self, name: str, speed: float = 1.0) -> bool:
        """
        Chạy motor lùi

        Args:
            name: Device name
            speed: Tốc độ từ 0.0 - 1.0 (0% - 100%)
        """
        device_key = name.lower().strip()

        if device_key not in self.devices:
            logger.warning(f"Không tìm thấy motor: '{name}'")
            return False

        # Clamp speed 0-1
        speed = max(0.0, min(1.0, speed))

        if self.mock_mode:
            logger.info(f"[MOCK] Motor '{name}' chạy lùi {speed*100:.0f}%")
            self._states[device_key] = ("backward", speed)
            return True

        device = self.devices[device_key]
        if device is None or not isinstance(device, Motor):
            logger.warning(f"Device '{name}' không phải motor")
            return False

        try:
            device.backward(speed=speed)
            self._states[device_key] = ("backward", speed)
            logger.info(f"Motor '{name}' chạy lùi {speed*100:.0f}%")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi điều khiển motor '{name}': {e}")
            return False

    def motor_stop(self, name: str) -> bool:
        """Dừng motor"""
        device_key = name.lower().strip()

        if device_key not in self.devices:
            logger.warning(f"Không tìm thấy motor: '{name}'")
            return False

        if self.mock_mode:
            logger.info(f"[MOCK] Motor '{name}' dừng")
            self._states[device_key] = ("stop", 0)
            return True

        device = self.devices[device_key]
        if device is None or not isinstance(device, Motor):
            logger.warning(f"Device '{name}' không phải motor")
            return False

        try:
            device.stop()
            self._states[device_key] = ("stop", 0)
            logger.info(f"Motor '{name}' dừng")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi dừng motor '{name}': {e}")
            return False

    # ===== PWM Methods =====

    def pwm_set_duty_cycle(self, name: str, duty_cycle: float) -> bool:
        """
        Đặt PWM duty cycle

        Args:
            name: Device name
            duty_cycle: 0.0 - 1.0 (0% - 100%)
        """
        device_key = name.lower().strip()

        if device_key not in self.devices:
            logger.warning(f"Không tìm thấy PWM device: '{name}'")
            return False

        # Clamp 0-1
        duty_cycle = max(0.0, min(1.0, duty_cycle))

        if self.mock_mode:
            logger.info(f"[MOCK] PWM '{name}' -> {duty_cycle*100:.1f}%")
            self._states[device_key] = duty_cycle
            return True

        device = self.devices[device_key]
        if device is None or not isinstance(device, PWMOutputDevice):
            return False

        try:
            device.value = duty_cycle
            self._states[device_key] = duty_cycle
            logger.info(f"PWM '{name}' -> {duty_cycle*100:.1f}%")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi điều khiển PWM '{name}': {e}")
            return False

    # ===== Generic Methods =====

    def _turn_on(self, name: str, expected_type: DeviceType) -> bool:
        """Generic turn on method"""
        device_key = name.lower().strip()

        if device_key not in self.devices:
            logger.warning(f"Không tìm thấy device: '{name}'")
            return False

        if self.mock_mode:
            logger.info(f"[MOCK] Bật {expected_type.value} '{name}'")
            self._states[device_key] = True
            return True

        device = self.devices[device_key]
        if device is None:
            return False

        try:
            device.on()
            self._states[device_key] = True
            logger.info(f"Đã bật {expected_type.value} '{name}'")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi bật {expected_type.value} '{name}': {e}")
            return False

    def _turn_off(self, name: str, expected_type: DeviceType) -> bool:
        """Generic turn off method"""
        device_key = name.lower().strip()

        if device_key not in self.devices:
            logger.warning(f"Không tìm thấy device: '{name}'")
            return False

        if self.mock_mode:
            logger.info(f"[MOCK] Tắt {expected_type.value} '{name}'")
            self._states[device_key] = False
            return True

        device = self.devices[device_key]
        if device is None:
            return False

        try:
            device.off()
            self._states[device_key] = False
            logger.info(f"Đã tắt {expected_type.value} '{name}'")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi tắt {expected_type.value} '{name}': {e}")
            return False

    def get_state(self, name: str) -> Union[bool, float]:
        """Lấy trạng thái device"""
        device_key = name.lower().strip()
        return self._states.get(device_key, False)

    def get_all_states(self) -> Dict[str, Union[bool, float]]:
        """Lấy trạng thái tất cả devices"""
        return self._states.copy()

    def cleanup(self) -> None:
        """Cleanup và release GPIO pins"""
        if self.mock_mode:
            logger.info("[MOCK] Cleanup GPIO devices")
            return

        for device_key, device in self.devices.items():
            if device is not None:
                try:
                    # Turn off/reset device
                    if isinstance(device, Servo):
                        device.mid()  # Center servo
                    elif isinstance(device, PWMOutputDevice):
                        device.value = 0
                    elif isinstance(device, Motor):
                        device.stop()
                    else:
                        device.off()

                    device.close()
                    logger.info(f"Đã cleanup device '{device_key}'")
                except Exception as e:
                    logger.error(f"Lỗi cleanup device '{device_key}': {e}")

        self.devices.clear()
        logger.info("GPIO devices cleanup hoàn tất")
