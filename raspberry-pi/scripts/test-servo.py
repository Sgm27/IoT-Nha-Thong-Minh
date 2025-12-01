#!/usr/bin/env python3
"""
Test servo motor on GPIO18
Moves servo through full range of motion
"""

import sys
import time
from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory

def test_servo_basic(gpio_pin=18):
    """Test servo with basic gpiozero (may have jitter)"""

    print("=" * 50)
    print("  Servo Motor Test - Basic Mode")
    print("=" * 50)
    print()
    print(f"Testing servo on GPIO{gpio_pin}")
    print("⚠️  Using software PWM (may jitter)")
    print()

    try:
        servo = Servo(gpio_pin)

        print("Test 1: Move to MINIMUM position (0°)")
        servo.min()
        print("  ✅ Servo should be at 0° (fully counter-clockwise)")
        time.sleep(2)

        print()
        print("Test 2: Move to CENTER position (90°)")
        servo.mid()
        print("  ✅ Servo should be at 90° (center)")
        time.sleep(2)

        print()
        print("Test 3: Move to MAXIMUM position (180°)")
        servo.max()
        print("  ✅ Servo should be at 180° (fully clockwise)")
        time.sleep(2)

        print()
        print("Test 4: Sweep test (0° → 180° → 0°)")
        for i in range(5):
            servo.min()
            time.sleep(0.5)
            servo.max()
            time.sleep(0.5)

        print("  ✅ Sweep complete")

        # Return to center
        print()
        print("Returning to center position...")
        servo.mid()
        time.sleep(1)

        # Cleanup
        servo.close()

        print()
        print("=" * 50)
        print("✅ SUCCESS: Servo test complete!")
        print("=" * 50)
        print()
        print("If servo jittered or shook:")
        print("  Run: sudo apt install pigpio python3-pigpio")
        print("  Then: sudo systemctl enable pigpiod && sudo systemctl start pigpiod")
        print("  Then run: sudo python3 scripts/test-servo.py --pigpio")
        print()

        return True

    except Exception as e:
        print()
        print("=" * 50)
        print(f"❌ FAILED: {e}")
        print("=" * 50)
        print()
        print("Troubleshooting:")
        print("  1. Check servo is connected to GPIO18 (Pin 12)")
        print("  2. Check power connection (Red to 5V, Brown to GND)")
        print("  3. Make sure running with sudo")
        print("  4. Try different servo (might be broken)")
        print()
        return False


def test_servo_pigpio(gpio_pin=18):
    """Test servo with pigpio (hardware PWM, no jitter)"""

    print("=" * 50)
    print("  Servo Motor Test - Hardware PWM Mode")
    print("=" * 50)
    print()
    print(f"Testing servo on GPIO{gpio_pin}")
    print("✅ Using hardware PWM (pigpio) - no jitter!")
    print()

    try:
        # Use pigpio factory for hardware PWM
        factory = PiGPIOFactory()
        servo = Servo(gpio_pin, pin_factory=factory)

        print("Test 1: Move to MINIMUM position (0°)")
        servo.min()
        print("  ✅ Servo at 0°")
        time.sleep(2)

        print()
        print("Test 2: Move to CENTER position (90°)")
        servo.mid()
        print("  ✅ Servo at 90°")
        time.sleep(2)

        print()
        print("Test 3: Move to MAXIMUM position (180°)")
        servo.max()
        print("  ✅ Servo at 180°")
        time.sleep(2)

        print()
        print("Test 4: Fine position control")
        positions = [-1.0, -0.5, 0, 0.5, 1.0]
        angles = [0, 45, 90, 135, 180]

        for pos, angle in zip(positions, angles):
            print(f"  Moving to {angle}°...")
            servo.value = pos
            time.sleep(1)

        print("  ✅ Fine control complete")

        # Return to center
        print()
        print("Returning to center position...")
        servo.mid()
        time.sleep(1)

        # Cleanup
        servo.close()

        print()
        print("=" * 50)
        print("✅ SUCCESS: Hardware PWM test complete!")
        print("=" * 50)
        print()
        print("Servo should have moved smoothly with no jitter!")
        print()

        return True

    except ImportError:
        print()
        print("=" * 50)
        print("❌ pigpio not installed!")
        print("=" * 50)
        print()
        print("Install with:")
        print("  sudo apt install pigpio python3-pigpio")
        print("  sudo systemctl enable pigpiod")
        print("  sudo systemctl start pigpiod")
        print()
        return False

    except Exception as e:
        print()
        print("=" * 50)
        print(f"❌ FAILED: {e}")
        print("=" * 50)
        print()
        print("Make sure pigpiod daemon is running:")
        print("  sudo systemctl start pigpiod")
        print("  sudo systemctl status pigpiod")
        print()
        return False


def interactive_test(gpio_pin=18, use_pigpio=False):
    """Interactive servo control"""

    print("=" * 50)
    print("  Interactive Servo Control")
    print("=" * 50)
    print()

    try:
        if use_pigpio:
            factory = PiGPIOFactory()
            servo = Servo(gpio_pin, pin_factory=factory)
            print("Using hardware PWM (pigpio)")
        else:
            servo = Servo(gpio_pin)
            print("Using software PWM")

        print()
        print("Commands:")
        print("  0-180  : Move to specific angle")
        print("  min    : Move to 0°")
        print("  mid    : Move to 90°")
        print("  max    : Move to 180°")
        print("  sweep  : Sweep back and forth")
        print("  q      : Quit")
        print()

        while True:
            try:
                cmd = input("Enter command: ").strip().lower()

                if cmd == 'q' or cmd == 'quit':
                    break
                elif cmd == 'min':
                    servo.min()
                    print("  → Moved to 0°")
                elif cmd == 'mid':
                    servo.mid()
                    print("  → Moved to 90°")
                elif cmd == 'max':
                    servo.max()
                    print("  → Moved to 180°")
                elif cmd == 'sweep':
                    print("  Sweeping...")
                    for _ in range(3):
                        servo.min()
                        time.sleep(0.5)
                        servo.max()
                        time.sleep(0.5)
                    servo.mid()
                    print("  → Sweep complete")
                else:
                    # Try parsing as angle
                    try:
                        angle = int(cmd)
                        if 0 <= angle <= 180:
                            # Convert angle to servo value (-1 to 1)
                            value = (angle / 90.0) - 1.0
                            servo.value = value
                            print(f"  → Moved to {angle}°")
                        else:
                            print("  ❌ Angle must be 0-180")
                    except ValueError:
                        print("  ❌ Invalid command")

            except KeyboardInterrupt:
                break

        # Return to center and cleanup
        servo.mid()
        servo.close()
        print()
        print("Done!")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test servo motor")
    parser.add_argument("--gpio", type=int, default=18, help="GPIO pin (default: 18)")
    parser.add_argument("--pigpio", action="store_true", help="Use hardware PWM (requires pigpio)")
    parser.add_argument("--interactive", action="store_true", help="Interactive control mode")

    args = parser.parse_args()

    # Check if running with sudo
    import os
    if os.geteuid() != 0:
        print("❌ This script must be run with sudo!")
        print("   Run: sudo python3 scripts/test-servo.py")
        sys.exit(1)

    if args.interactive:
        interactive_test(args.gpio, args.pigpio)
    elif args.pigpio:
        success = test_servo_pigpio(args.gpio)
    else:
        success = test_servo_basic(args.gpio)

    sys.exit(0 if success else 1)
