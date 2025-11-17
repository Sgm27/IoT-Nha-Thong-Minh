"""
Example GPIO devices configuration
Cấu hình các thiết bị GPIO: LED, Buzzer, Servo, Relay
"""

from src.gpio_devices import GPIODeviceConfig, DeviceType

# ===== LED Configuration =====
led_devices = {
    "LED Đỏ": GPIODeviceConfig(
        gpio_pin=17,
        name="LED Đỏ",
        device_type=DeviceType.LED,
        active_high=True  # LED thường active HIGH
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
}

# ===== Buzzer Configuration =====
buzzer_devices = {
    "Buzzer Cảnh báo": GPIODeviceConfig(
        gpio_pin=23,
        name="Buzzer Cảnh báo",
        device_type=DeviceType.BUZZER,
        active_high=True
    ),
}

# ===== Servo Configuration =====
servo_devices = {
    "Servo Cửa": GPIODeviceConfig(
        gpio_pin=18,  # GPIO 18 support hardware PWM
        name="Servo Cửa",
        device_type=DeviceType.SERVO,
        # Servo SG90 standard values:
        min_pulse_width=0.5/1000,   # 0.5ms = 0°
        max_pulse_width=2.5/1000,   # 2.5ms = 180°
        frame_width=20.0/1000       # 20ms (50Hz)
    ),
    "Servo Camera": GPIODeviceConfig(
        gpio_pin=13,  # GPIO 13 support hardware PWM
        name="Servo Camera",
        device_type=DeviceType.SERVO,
    ),
}

# ===== Relay Configuration (nếu có) =====
relay_devices = {
    "Relay 1": GPIODeviceConfig(
        gpio_pin=24,
        name="Relay Đèn",
        device_type=DeviceType.RELAY,
        active_high=False  # Relay module thường active LOW
    ),
}

# ===== Combined Configuration =====
# Gộp tất cả devices lại
all_devices = {
    **led_devices,
    **buzzer_devices,
    **servo_devices,
    # **relay_devices,  # Uncomment nếu có relay
}

# ===== Pin Reference cho Raspberry Pi 5 =====
"""
Raspberry Pi 5 GPIO Pinout (BCM numbering):

PWM-capable pins (cho Servo):
- GPIO 12, 13 (PWM0)
- GPIO 18, 19 (PWM1)

Recommended pin assignment:
┌─────────────────────────────────────────┐
│ Device Type  │ GPIO Pin │ Description  │
├─────────────────────────────────────────┤
│ LED Đỏ       │ GPIO 17  │ Active HIGH  │
│ LED Xanh     │ GPIO 27  │ Active HIGH  │
│ LED Vàng     │ GPIO 22  │ Active HIGH  │
│ Buzzer       │ GPIO 23  │ Active HIGH  │
│ Servo 1      │ GPIO 18  │ PWM (50Hz)   │
│ Servo 2      │ GPIO 13  │ PWM (50Hz)   │
│ Relay 1      │ GPIO 24  │ Active LOW   │
│ Relay 2      │ GPIO 25  │ Active LOW   │
└─────────────────────────────────────────┘

Wiring Notes:
- LED: GPIO → 330Ω Resistor → LED+ → LED- → GND
- Buzzer: GPIO → Buzzer+ → Buzzer- → GND (hoặc ngược lại tùy loại)
- Servo: GPIO → Signal, 5V → VCC, GND → GND
- Relay: GPIO → IN, VCC → 5V, GND → GND
"""
