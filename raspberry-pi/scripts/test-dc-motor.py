#!/usr/bin/env python3
"""
Test DC motor with L298N motor driver
Tests forward, backward, and speed control
"""

import sys
import time
from gpiozero import Motor
import argparse

def test_dc_motor_basic(forward_pin=16, backward_pin=20, enable_pin=18):
    """Test DC motor with L298N driver"""

    print("=" * 50)
    print("  DC Motor Test - L298N Driver")
    print("=" * 50)
    print()
    print(f"Pins configured:")
    print(f"  Forward (IN1):  GPIO{forward_pin}")
    print(f"  Backward (IN2): GPIO{backward_pin}")
    print(f"  Enable (ENA):   GPIO{enable_pin}")
    print()

    try:
        # Create motor object
        motor = Motor(forward=forward_pin, backward=backward_pin, enable=enable_pin)

        print("Test 1: Forward (full speed)")
        print("  Motor should spin in one direction at full speed")
        motor.forward()
        time.sleep(3)

        print()
        print("Test 2: Stop")
        motor.stop()
        time.sleep(1)

        print()
        print("Test 3: Backward (full speed)")
        print("  Motor should spin in opposite direction")
        motor.backward()
        time.sleep(3)

        print()
        print("Test 4: Stop")
        motor.stop()
        time.sleep(1)

        print()
        print("Test 5: Speed control (20% → 100%)")
        for speed in [0.2, 0.4, 0.6, 0.8, 1.0]:
            print(f"  Speed: {speed*100}%")
            motor.forward(speed=speed)
            time.sleep(1.5)

        motor.stop()
        time.sleep(1)

        print()
        print("Test 6: Gradual acceleration/deceleration")
        print("  Accelerating...")
        for speed in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
            motor.forward(speed=speed)
            time.sleep(0.3)

        print("  Decelerating...")
        for speed in [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]:
            motor.forward(speed=speed)
            time.sleep(0.3)

        motor.stop()
        motor.close()

        print()
        print("=" * 50)
        print("✅ SUCCESS: DC motor test complete!")
        print("=" * 50)
        print()
        print("If motor didn't move:")
        print("  1. Check L298N wiring (see DC_MOTOR_SETUP.md)")
        print("  2. Verify common ground (Pi GND ↔ L298N GND)")
        print("  3. Check external power supply is connected")
        print("  4. Verify jumper on ENA pin is removed")
        print()

        return True

    except Exception as e:
        print()
        print("=" * 50)
        print(f"❌ FAILED: {e}")
        print("=" * 50)
        print()
        print("Troubleshooting:")
        print("  1. Check L298N is connected to GPIO pins:")
        print(f"     - ENA → GPIO{enable_pin} (Pin 12)")
        print(f"     - IN1 → GPIO{forward_pin} (Pin 16)")
        print(f"     - IN2 → GPIO{backward_pin} (Pin 18)")
        print("  2. Check power connections:")
        print("     - External power (+) → L298N 12V")
        print("     - External power (-) → L298N GND")
        print("     - L298N GND → Pi GND (CRITICAL!)")
        print("  3. Make sure running with sudo")
        print("  4. Check motor wires connected to OUT1/OUT2")
        print()
        return False


def interactive_test(forward_pin=16, backward_pin=20, enable_pin=18):
    """Interactive DC motor control"""

    print("=" * 50)
    print("  Interactive DC Motor Control")
    print("=" * 50)
    print()

    try:
        motor = Motor(forward=forward_pin, backward=backward_pin, enable=enable_pin)

        print("Commands:")
        print("  f       : Forward (full speed)")
        print("  b       : Backward (full speed)")
        print("  s       : Stop")
        print("  0-100   : Set speed percentage (e.g., '50' for 50%)")
        print("  f50     : Forward at 50% speed")
        print("  b75     : Backward at 75% speed")
        print("  q       : Quit")
        print()

        current_speed = 1.0
        current_direction = None

        while True:
            try:
                cmd = input("Enter command: ").strip().lower()

                if cmd == 'q' or cmd == 'quit':
                    break
                elif cmd == 'f':
                    motor.forward(speed=current_speed)
                    current_direction = "forward"
                    print(f"  → Motor forward at {current_speed*100}%")
                elif cmd == 'b':
                    motor.backward(speed=current_speed)
                    current_direction = "backward"
                    print(f"  → Motor backward at {current_speed*100}%")
                elif cmd == 's' or cmd == 'stop':
                    motor.stop()
                    current_direction = None
                    print("  → Motor stopped")
                elif cmd.startswith('f') and len(cmd) > 1:
                    # Forward with speed (e.g., "f50")
                    try:
                        speed = int(cmd[1:])
                        if 0 <= speed <= 100:
                            speed_val = speed / 100.0
                            motor.forward(speed=speed_val)
                            current_speed = speed_val
                            current_direction = "forward"
                            print(f"  → Motor forward at {speed}%")
                        else:
                            print("  ❌ Speed must be 0-100")
                    except ValueError:
                        print("  ❌ Invalid speed value")
                elif cmd.startswith('b') and len(cmd) > 1:
                    # Backward with speed (e.g., "b75")
                    try:
                        speed = int(cmd[1:])
                        if 0 <= speed <= 100:
                            speed_val = speed / 100.0
                            motor.backward(speed=speed_val)
                            current_speed = speed_val
                            current_direction = "backward"
                            print(f"  → Motor backward at {speed}%")
                        else:
                            print("  ❌ Speed must be 0-100")
                    except ValueError:
                        print("  ❌ Invalid speed value")
                else:
                    # Try parsing as speed percentage
                    try:
                        speed = int(cmd)
                        if 0 <= speed <= 100:
                            speed_val = speed / 100.0
                            current_speed = speed_val

                            if current_direction == "forward":
                                motor.forward(speed=speed_val)
                                print(f"  → Speed changed to {speed}% (forward)")
                            elif current_direction == "backward":
                                motor.backward(speed=speed_val)
                                print(f"  → Speed changed to {speed}% (backward)")
                            else:
                                print(f"  → Speed set to {speed}% (motor stopped)")
                        else:
                            print("  ❌ Speed must be 0-100")
                    except ValueError:
                        print("  ❌ Invalid command")

            except KeyboardInterrupt:
                break

        # Stop and cleanup
        motor.stop()
        motor.close()
        print()
        print("Done!")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test DC motor with L298N driver")
    parser.add_argument("--forward", type=int, default=16, help="Forward pin (IN1, default: 16)")
    parser.add_argument("--backward", type=int, default=20, help="Backward pin (IN2, default: 20)")
    parser.add_argument("--enable", type=int, default=18, help="Enable pin (ENA, default: 18)")
    parser.add_argument("--interactive", action="store_true", help="Interactive control mode")

    args = parser.parse_args()

    # Check if running with sudo
    import os
    if os.geteuid() != 0:
        print("❌ This script must be run with sudo!")
        print("   Run: sudo python3 scripts/test-dc-motor.py")
        sys.exit(1)

    if args.interactive:
        interactive_test(args.forward, args.backward, args.enable)
    else:
        success = test_dc_motor_basic(args.forward, args.backward, args.enable)
        sys.exit(0 if success else 1)
