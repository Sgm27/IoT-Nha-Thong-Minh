#!/usr/bin/env python3
"""
Hardware Test Script - Test LED và Buzzer
Chạy trên Raspberry Pi để kiểm tra kết nối phần cứng
"""

import sys
import time
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gpio_devices import GPIODevicesController, GPIODeviceConfig, DeviceType


def print_banner(text):
    """In banner đẹp"""
    print("\n" + "=" * 50)
    print(f"  {text}")
    print("=" * 50)


def test_led(gpio, name, pin):
    """Test một LED"""
    print(f"\n🔴 Testing {name} (GPIO{pin})...")
    print(f"   LED should BLINK 3 times...")

    try:
        for i in range(3):
            print(f"   Blink {i+1}/3: ON", end="", flush=True)
            gpio.led_on(name)
            time.sleep(0.5)

            print(" → OFF", flush=True)
            gpio.led_off(name)
            time.sleep(0.5)

        print(f"✅ {name} test completed!")
        return True
    except Exception as e:
        print(f"❌ {name} test FAILED: {e}")
        return False


def test_buzzer(gpio, name, pin):
    """Test buzzer"""
    print(f"\n🔊 Testing {name} (GPIO{pin})...")
    print(f"   Buzzer should BEEP 3 times...")

    try:
        # Test 3 beeps
        print(f"   Beeping 3 times...", flush=True)
        gpio.buzzer_beep(name, on_time=0.2, off_time=0.2, n=3)
        time.sleep(2)  # Wait for beeps to finish

        print(f"✅ {name} test completed!")
        return True
    except Exception as e:
        print(f"❌ {name} test FAILED: {e}")
        return False


def test_servo(gpio, name, pin):
    """Test servo"""
    print(f"\n🔄 Testing {name} (GPIO{pin})...")
    print(f"   Servo should sweep 0° → 90° → 180° → 90°...")

    try:
        angles = [0, 45, 90, 135, 180, 90]
        for angle in angles:
            print(f"   Moving to {angle}°...", flush=True)
            gpio.servo_set_angle(name, angle)
            time.sleep(0.5)

        print(f"✅ {name} test completed!")
        return True
    except Exception as e:
        print(f"❌ {name} test FAILED: {e}")
        return False


def main():
    print_banner("🧪 Hardware Test Script")
    print("\nThis script will test all connected hardware:")
    print("  - LEDs will blink 3 times")
    print("  - Buzzer will beep 3 times")
    print("  - Servo will sweep through angles")
    print("\nWatch your hardware to verify it's working!\n")

    input("Press ENTER to start testing...")

    # Configuration - Giống như trong iot_client.py
    devices = {
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
        "Buzzer": GPIODeviceConfig(
            gpio_pin=23,
            name="Buzzer Cảnh báo",
            device_type=DeviceType.BUZZER,
            active_high=True
        ),
        "Servo Cửa": GPIODeviceConfig(
            gpio_pin=18,
            name="Servo Cửa",
            device_type=DeviceType.SERVO,
        ),
    }

    # Initialize GPIO controller
    print_banner("Initializing GPIO Controller")
    try:
        gpio = GPIODevicesController(devices, mock_mode=False)
        print("✅ GPIO Controller initialized!")
    except Exception as e:
        print(f"❌ Failed to initialize GPIO: {e}")
        print("\nPossible issues:")
        print("  - Not running on Raspberry Pi")
        print("  - No permission (run with sudo)")
        print("  - gpiozero not installed")
        sys.exit(1)

    # Test results
    results = {}

    try:
        # Test LEDs
        print_banner("Testing LEDs")
        results["LED Đỏ"] = test_led(gpio, "LED Đỏ", 17)
        time.sleep(1)

        results["LED Xanh"] = test_led(gpio, "LED Xanh", 27)
        time.sleep(1)

        results["LED Vàng"] = test_led(gpio, "LED Vàng", 22)
        time.sleep(1)

        # Test Buzzer
        print_banner("Testing Buzzer")
        results["Buzzer"] = test_buzzer(gpio, "Buzzer", 23)
        time.sleep(1)

        # Test Servo
        print_banner("Testing Servo")
        results["Servo Cửa"] = test_servo(gpio, "Servo Cửa", 18)
        time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    finally:
        # Cleanup
        print_banner("Cleanup")
        gpio.cleanup()
        print("✅ GPIO cleaned up")

    # Summary
    print_banner("Test Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for device, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {device:20s} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests PASSED! Hardware is working correctly!")
    else:
        print("\n⚠️  Some tests FAILED. Check wiring and troubleshooting guide.")
        print("\nCommon issues:")
        print("  - LED not blinking → Check polarity (long leg = +)")
        print("  - LED not blinking → Check resistor 330Ω is connected")
        print("  - Buzzer not beeping → Try reversing +/- connections")
        print("  - Servo not moving → Check it's on GPIO18 (PWM pin)")
        print("  - Servo not moving → Check 5V power is connected")


if __name__ == "__main__":
    main()
