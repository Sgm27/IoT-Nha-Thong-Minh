#!/bin/bash
# Simple hardware test script - Test từng device đơn giản nhất

echo "======================================"
echo "  Simple Hardware Test"
echo "======================================"
echo ""
echo "Chọn device cần test:"
echo "  1) LED Đỏ (GPIO17)"
echo "  2) LED Xanh (GPIO27)"
echo "  3) LED Vàng (GPIO22)"
echo "  4) Buzzer (GPIO23)"
echo "  5) Servo (GPIO18)"
echo "  6) Test tất cả"
echo "  0) Exit"
echo ""
read -p "Nhập số (0-6): " choice

case $choice in
    1)
        echo "Testing LED Đỏ (GPIO17)..."
        python3 << 'EOF'
from gpiozero import LED
import time

led = LED(17)
print("LED will blink 5 times...")
for i in range(5):
    print(f"Blink {i+1}/5: ON")
    led.on()
    time.sleep(0.5)
    print("       OFF")
    led.off()
    time.sleep(0.5)
print("✅ Done! Did you see the LED blink?")
led.close()
EOF
        ;;

    2)
        echo "Testing LED Xanh (GPIO27)..."
        python3 << 'EOF'
from gpiozero import LED
import time

led = LED(27)
print("LED will blink 5 times...")
for i in range(5):
    print(f"Blink {i+1}/5: ON")
    led.on()
    time.sleep(0.5)
    print("       OFF")
    led.off()
    time.sleep(0.5)
print("✅ Done! Did you see the LED blink?")
led.close()
EOF
        ;;

    3)
        echo "Testing LED Vàng (GPIO22)..."
        python3 << 'EOF'
from gpiozero import LED
import time

led = LED(22)
print("LED will blink 5 times...")
for i in range(5):
    print(f"Blink {i+1}/5: ON")
    led.on()
    time.sleep(0.5)
    print("       OFF")
    led.off()
    time.sleep(0.5)
print("✅ Done! Did you see the LED blink?")
led.close()
EOF
        ;;

    4)
        echo "Testing Buzzer (GPIO23)..."
        python3 << 'EOF'
from gpiozero import Buzzer
import time

buzzer = Buzzer(23)
print("Buzzer will beep 3 times...")
buzzer.beep(on_time=0.2, off_time=0.2, n=3, background=False)
print("✅ Done! Did you hear the buzzer?")
buzzer.close()
EOF
        ;;

    5)
        echo "Testing Servo (GPIO18)..."
        python3 << 'EOF'
from gpiozero import Servo
import time

servo = Servo(18)
print("Servo will sweep 0° → 90° → 180°...")
print("Moving to 0° (min)...")
servo.min()
time.sleep(1)
print("Moving to 90° (mid)...")
servo.mid()
time.sleep(1)
print("Moving to 180° (max)...")
servo.max()
time.sleep(1)
print("Back to 90° (center)...")
servo.mid()
time.sleep(1)
print("✅ Done! Did you see the servo move?")
servo.close()
EOF
        ;;

    6)
        echo "Testing ALL devices..."
        cd "$(dirname "$0")/.."
        python3 scripts/test-hardware.py
        ;;

    0)
        echo "Exiting..."
        exit 0
        ;;

    *)
        echo "Invalid choice!"
        exit 1
        ;;
esac

echo ""
echo "Test completed!"
