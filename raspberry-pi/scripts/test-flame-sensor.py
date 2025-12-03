#!/usr/bin/env python3
"""
Script test cảm biến lửa
Chạy: python scripts/test-flame-sensor.py
"""

import time
import sys

# GPIO pin cho cảm biến lửa
FLAME_SENSOR_PIN = 24

def test_with_gpiozero():
    """Test sử dụng gpiozero library"""
    try:
        from gpiozero import DigitalInputDevice
        print("✓ gpiozero đã được import thành công")
    except ImportError:
        print("✗ Không thể import gpiozero")
        print("  Cài đặt: pip install gpiozero")
        return False

    try:
        # Tạo sensor - module đã có pull-up riêng nên không cần internal pull-up
        sensor = DigitalInputDevice(FLAME_SENSOR_PIN, pull_up=False)
        print(f"✓ Đã khởi tạo cảm biến trên GPIO{FLAME_SENSOR_PIN}")
    except Exception as e:
        print(f"✗ Lỗi khởi tạo GPIO: {e}")
        return False

    print("\n" + "="*50)
    print("BẮT ĐẦU TEST CẢM BIẾN LỬA")
    print("="*50)
    print("- Đưa ngọn lửa (bật lửa) vào trước cảm biến")
    print("- Khoảng cách: 10-80cm")
    print("- Góc: trong vùng 60 độ trước cảm biến")
    print("- Nhấn Ctrl+C để dừng")
    print("="*50 + "\n")

    fire_count = 0
    total_count = 0

    try:
        while True:
            # Đọc giá trị: 0 = có lửa, 1 = không có lửa
            raw_value = sensor.value
            fire_detected = raw_value == 0

            total_count += 1

            if fire_detected:
                fire_count += 1
                print(f"\r🔥 [{total_count:5d}] PHÁT HIỆN LỬA! (Tổng: {fire_count} lần)        ", end="")
            else:
                print(f"\r✓ [{total_count:5d}] Bình thường - Không có lửa                    ", end="")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\n" + "="*50)
        print("KẾT QUẢ TEST")
        print("="*50)
        print(f"Tổng số lần đọc: {total_count}")
        print(f"Số lần phát hiện lửa: {fire_count}")
        if total_count > 0:
            print(f"Tỷ lệ phát hiện: {fire_count/total_count*100:.1f}%")
        print("="*50)

    finally:
        sensor.close()
        print("Đã đóng GPIO")

    return True


def test_mock_mode():
    """Test ở chế độ mock (không cần hardware)"""
    print("="*50)
    print("TEST CHẾ ĐỘ MOCK (không cần phần cứng)")
    print("="*50)

    # Import từ src
    sys.path.insert(0, 'src')
    try:
        from gpio_devices import GPIODevicesController, GPIODeviceConfig, DeviceType
        from flame_sensor_service import FlameSensorService, FlameSensorConfig, FireDetectionResult
    except ImportError as e:
        print(f"✗ Lỗi import: {e}")
        print("  Chạy từ thư mục raspberry-pi/")
        return False

    # Tạo config
    gpio_configs = {
        "Test Sensor": GPIODeviceConfig(
            gpio_pin=24,
            name="Test Sensor",
            device_type=DeviceType.FLAME_SENSOR,
        ),
        "Buzzer": GPIODeviceConfig(
            gpio_pin=23,
            name="Buzzer",
            device_type=DeviceType.BUZZER,
        ),
    }

    # Tạo controller ở mock mode
    gpio = GPIODevicesController(gpio_configs, mock_mode=True)
    print("✓ GPIO Controller (mock mode)")

    # Tạo flame sensor service
    flame_service = FlameSensorService(
        gpio_controller=gpio,
        config=FlameSensorConfig(
            poll_interval=0.5,
            confirm_readings=2,
            alert_cooldown=5.0,
        ),
        mock_mode=True
    )
    print("✓ Flame Sensor Service (mock mode)")

    # Set callback
    def on_fire_alert(result: FireDetectionResult):
        print(f"\n🔥 ALERT: {result.message}")
        print(f"   Level: {result.level.value}")
        print(f"   Consecutive: {result.consecutive_count}")

    flame_service.set_fire_alert_callback(on_fire_alert)

    # Trigger test alert
    print("\n--- Triggering test alert ---")
    flame_service.trigger_test_alert("Mock Sensor")

    print("\n✓ Mock test hoàn tất")
    return True


def main():
    print("\n" + "="*50)
    print("TEST MODULE CẢM BIẾN LỬA")
    print("="*50 + "\n")

    print("Chọn chế độ test:")
    print("1. Test với phần cứng thật (cần GPIO)")
    print("2. Test mock mode (không cần phần cứng)")
    print()

    choice = input("Nhập lựa chọn (1/2): ").strip()

    if choice == "1":
        test_with_gpiozero()
    elif choice == "2":
        test_mock_mode()
    else:
        print("Lựa chọn không hợp lệ")
        # Mặc định thử với gpiozero
        print("Thử test với gpiozero...")
        try:
            test_with_gpiozero()
        except Exception as e:
            print(f"Lỗi: {e}")
            print("Chuyển sang mock mode...")
            test_mock_mode()


if __name__ == "__main__":
    main()
