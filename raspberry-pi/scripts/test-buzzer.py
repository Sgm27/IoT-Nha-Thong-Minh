#!/usr/bin/env python3
"""
Simple script to test buzzer on Raspberry Pi
"""

import sys
import time
from gpiozero import Buzzer

def test_buzzer(gpio_pin=23):
    """Test buzzer at GPIO pin"""

    print("=" * 50)
    print("  Buzzer Test Script")
    print("=" * 50)
    print()

    print(f"Testing buzzer at GPIO{gpio_pin}...")
    print()

    try:
        # Create buzzer object
        buzzer = Buzzer(gpio_pin)

        # Test 1: Simple beep
        print("Test 1: Single beep (0.5 seconds)")
        buzzer.on()
        time.sleep(0.5)
        buzzer.off()
        print("  ✅ Done")
        time.sleep(1)

        # Test 2: Multiple beeps
        print()
        print("Test 2: Beep 3 times")
        buzzer.beep(on_time=0.2, off_time=0.2, n=3, background=False)
        print("  ✅ Done")
        time.sleep(1)

        # Test 3: Fire alert pattern (5 rapid beeps)
        print()
        print("Test 3: Fire alert pattern (5 rapid beeps)")
        buzzer.beep(on_time=0.2, off_time=0.1, n=5, background=False)
        print("  ✅ Done")

        # Cleanup
        buzzer.close()

        print()
        print("=" * 50)
        print("✅ SUCCESS: Buzzer is working!")
        print()
        print("If you heard beeping sounds, the buzzer works perfectly.")
        print()
        return True

    except Exception as e:
        print()
        print("=" * 50)
        print(f"❌ FAILED: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Check buzzer is connected to GPIO23")
        print("  2. Check positive wire goes to GPIO23")
        print("  3. Check negative wire goes to GND")
        print("  4. Make sure you're running with sudo")
        print()
        return False


if __name__ == "__main__":
    gpio_pin = int(sys.argv[1]) if len(sys.argv) > 1 else 23

    print("⚠️  Make sure buzzer is connected before continuing!")
    print(f"   Buzzer should be on GPIO{gpio_pin}")
    print()
    input("Press Enter to start test...")
    print()

    success = test_buzzer(gpio_pin)
    sys.exit(0 if success else 1)
