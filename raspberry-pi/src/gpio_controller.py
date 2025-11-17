"""
GPIO Controller cho Raspberry Pi 5
Điều khiển relay module 4 kênh để bật/tắt đèn
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass

try:
    from gpiozero import OutputDevice
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("gpiozero không khả dụng - chạy ở chế độ mock")


logger = logging.getLogger(__name__)


@dataclass
class RelayConfig:
    """Cấu hình cho một relay"""
    gpio_pin: int
    location: str
    active_high: bool = False  # Relay thường dùng active LOW


class GPIOController:
    """
    Điều khiển GPIO pins cho relay module

    Relay module 4 kênh thường hoạt động ở chế độ active LOW:
    - GPIO HIGH (3.3V) = Relay OFF
    - GPIO LOW (0V) = Relay ON
    """

    def __init__(self, relay_configs: Dict[str, RelayConfig], mock_mode: bool = False):
        """
        Args:
            relay_configs: Dict mapping location name -> RelayConfig
            mock_mode: Nếu True, không điều khiển GPIO thực (để test)
        """
        self.relay_configs = relay_configs
        self.mock_mode = mock_mode or not GPIO_AVAILABLE
        self.relays: Dict[str, Optional[OutputDevice]] = {}
        self._states: Dict[str, bool] = {}

        self._initialize_relays()

    def _initialize_relays(self) -> None:
        """Khởi tạo tất cả relay pins"""
        for location, config in self.relay_configs.items():
            location_key = location.lower().strip()

            if self.mock_mode:
                logger.info(
                    f"[MOCK] Khởi tạo relay cho '{config.location}' "
                    f"(GPIO{config.gpio_pin}, active_high={config.active_high})"
                )
                self.relays[location_key] = None
                self._states[location_key] = False
            else:
                try:
                    # active_high=False nghĩa là relay bật khi pin LOW
                    relay = OutputDevice(
                        config.gpio_pin,
                        active_high=config.active_high,
                        initial_value=False  # Ban đầu tắt
                    )
                    self.relays[location_key] = relay
                    self._states[location_key] = False
                    logger.info(
                        f"Khởi tạo relay cho '{config.location}' tại GPIO{config.gpio_pin}"
                    )
                except Exception as e:
                    logger.error(f"Lỗi khởi tạo GPIO{config.gpio_pin} cho '{config.location}': {e}")
                    self.relays[location_key] = None
                    self._states[location_key] = False

    def turn_on(self, location: str) -> bool:
        """
        Bật relay (đèn sáng)

        Returns:
            True nếu thành công
        """
        location_key = location.lower().strip()

        if location_key not in self.relays:
            logger.warning(f"Không tìm thấy relay cho location: '{location}'")
            return False

        if self.mock_mode:
            logger.info(f"[MOCK] Bật đèn '{location}'")
            self._states[location_key] = True
            return True

        relay = self.relays[location_key]
        if relay is None:
            logger.warning(f"Relay cho '{location}' chưa được khởi tạo")
            return False

        try:
            relay.on()  # Với active_high=False, này sẽ set pin LOW -> relay ON
            self._states[location_key] = True
            logger.info(f"Đã bật đèn '{location}'")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi bật đèn '{location}': {e}")
            return False

    def turn_off(self, location: str) -> bool:
        """
        Tắt relay (đèn tắt)

        Returns:
            True nếu thành công
        """
        location_key = location.lower().strip()

        if location_key not in self.relays:
            logger.warning(f"Không tìm thấy relay cho location: '{location}'")
            return False

        if self.mock_mode:
            logger.info(f"[MOCK] Tắt đèn '{location}'")
            self._states[location_key] = False
            return True

        relay = self.relays[location_key]
        if relay is None:
            logger.warning(f"Relay cho '{location}' chưa được khởi tạo")
            return False

        try:
            relay.off()  # Với active_high=False, này sẽ set pin HIGH -> relay OFF
            self._states[location_key] = False
            logger.info(f"Đã tắt đèn '{location}'")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi tắt đèn '{location}': {e}")
            return False

    def get_state(self, location: str) -> bool:
        """Lấy trạng thái hiện tại của relay"""
        location_key = location.lower().strip()
        return self._states.get(location_key, False)

    def get_all_states(self) -> Dict[str, bool]:
        """Lấy trạng thái của tất cả relay"""
        return self._states.copy()

    def cleanup(self) -> None:
        """Dọn dẹp và release GPIO pins"""
        if self.mock_mode:
            logger.info("[MOCK] Cleanup GPIO")
            return

        for location_key, relay in self.relays.items():
            if relay is not None:
                try:
                    relay.off()  # Tắt tất cả relay trước khi cleanup
                    relay.close()
                    logger.info(f"Đã cleanup relay cho '{location_key}'")
                except Exception as e:
                    logger.error(f"Lỗi cleanup relay '{location_key}': {e}")

        self.relays.clear()
        logger.info("GPIO cleanup hoàn tất")
