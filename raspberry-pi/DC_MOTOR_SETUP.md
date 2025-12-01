# DC Motor Setup Guide - Raspberry Pi

Complete guide to connecting and controlling a DC motor (2-wire motor) for fans, pumps, or continuous rotation.

## ⚠️ CRITICAL WARNING

**NEVER connect a DC motor directly to Raspberry Pi GPIO pins!**

Why?
- GPIO pins can only provide **16mA max**
- DC motors draw **100mA to 2000mA+**
- Direct connection will **DESTROY your Raspberry Pi!**

**You MUST use a motor driver!**

---

## 📦 What You Need

### **Required:**
1. **DC Motor** (the 2-wire motor you have)
2. **Motor Driver Module** - One of these:
   - **L298N** (recommended, cheap ~$2-3, drives 2 motors)
   - **L9110S** (very cheap ~$1, drives 2 motors)
   - **L293D** (IC chip, needs circuit)
   - **Single transistor circuit** (DIY, for simple on/off only)
3. **External power supply** (4.5V-12V depending on motor)
4. **Jumper wires** (male-to-female)

### **Optional:**
5. Flyback diode (if making transistor circuit)
6. Resistor (1kΩ if making transistor circuit)

---

## 🔧 Option 1: L298N Motor Driver (RECOMMENDED)

### **Why L298N?**
- ✅ Very cheap ($2-3)
- ✅ Easy to use
- ✅ Controls 2 motors
- ✅ Supports PWM (speed control)
- ✅ Forward/reverse control
- ✅ Built-in voltage regulator

### **L298N Connections:**

```
L298N Module         Raspberry Pi         DC Motor        Power Supply
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ENA (Enable A)   →   GPIO18 (PWM)
IN1              →   GPIO23
IN2              →   GPIO24

OUT1             →   ────────────────→   Motor Wire 1
OUT2             →   ────────────────→   Motor Wire 2

GND              →   Pi GND (Pin 6)   ←──────────────   Power GND (-)
+12V             →                    ←──────────────   Power +12V (+)
+5V (output)     →   (optional) Can power Pi
```

### **Pin Layout on L298N:**

```
L298N Motor Driver (top view)
┌─────────────────────────────┐
│  [12V] [GND] [5V]           │ ← Power input
│                             │
│  [ENA]                      │ ← Enable Motor A (PWM speed)
│  [IN1] [IN2]                │ ← Control Motor A direction
│  [IN3] [IN4]                │ ← Control Motor B direction
│  [ENB]                      │ ← Enable Motor B
│                             │
│  [OUT1] [OUT2]              │ ← Motor A output
│  [OUT3] [OUT4]              │ ← Motor B output
└─────────────────────────────┘
```

### **Wiring Steps:**

1. **Power Supply to L298N:**
   - (+) → L298N **12V** (or 5V/6V/9V depending on your motor voltage)
   - (-) → L298N **GND**

2. **L298N to Raspberry Pi:**
   - L298N **GND** → Pi **Pin 6 (GND)** ← **VERY IMPORTANT!**
   - L298N **ENA** → Pi **Pin 12 (GPIO18)** for speed control
   - L298N **IN1** → Pi **Pin 16 (GPIO23)** for direction
   - L298N **IN2** → Pi **Pin 18 (GPIO24)** for direction

3. **DC Motor to L298N:**
   - Motor Wire 1 → L298N **OUT1**
   - Motor Wire 2 → L298N **OUT2**

**⚠️ Common Ground CRITICAL:** Pi GND and Power Supply GND MUST be connected!

---

## 🔧 Option 2: L9110S Motor Driver (Smaller, Cheaper)

### **L9110S Connections:**

```
L9110S Module        Raspberry Pi         DC Motor        Power Supply
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VCC              →   Pi 5V (Pin 2)    OR ────────────→   Power +5V
GND              →   Pi GND (Pin 6)   ←──────────────   Power GND

A-IA             →   GPIO23
A-IB             →   GPIO24

Motor A+         →   ────────────────→   Motor Wire 1
Motor A-         →   ────────────────→   Motor Wire 2
```

---

## 🔧 Option 3: Simple Transistor Circuit (ON/OFF Only)

**⚠️ Only for simple ON/OFF control, no speed control!**

### **Parts Needed:**
- 1x NPN Transistor (2N2222, BC547, or similar)
- 1x Diode (1N4007)
- 1x Resistor (1kΩ)

### **Circuit Diagram:**

```
                   Raspberry Pi
                   GPIO23 ──────┬─── [1kΩ Resistor] ───┬
                                │                       │
                   Pi GND ──────┼───────────────────────┼─── Motor (-) ─── Power GND (-)
                                │                       │
                                │                    [Base]
                                │                  Transistor
                                │                 [Collector]
                                │                       │
                                └───[Diode]─────────────┤
                                    (stripe to +)       │
                                                        │
                   Motor (+) ──────────────────────────┴─── Power Supply (+)
```

**This only allows ON/OFF, not speed control or direction!**

---

## 💻 Python Code Examples

### **Code for L298N Motor Driver:**

```python
from gpiozero import Motor, PWMOutputDevice
from time import sleep

# Create motor object
# Motor uses IN1 and IN2 for direction
motor = Motor(forward=23, backward=24, enable=18)

# Full speed forward
motor.forward()
sleep(2)

# Half speed forward
motor.forward(speed=0.5)
sleep(2)

# Stop
motor.stop()
sleep(1)

# Full speed backward
motor.backward()
sleep(2)

# Stop
motor.stop()

# Cleanup
motor.close()
```

### **Speed Control Example:**

```python
from gpiozero import Motor
from time import sleep

motor = Motor(forward=23, backward=24, enable=18)

# Gradual speed up
for speed in [0.2, 0.4, 0.6, 0.8, 1.0]:
    print(f"Speed: {speed*100}%")
    motor.forward(speed=speed)
    sleep(2)

motor.stop()
motor.close()
```

### **Simple ON/OFF (Transistor Circuit):**

```python
from gpiozero import OutputDevice
from time import sleep

# Simple on/off control
motor = OutputDevice(23)

# Turn on
motor.on()
sleep(5)

# Turn off
motor.off()

# Cleanup
motor.close()
```

---

## ✅ Testing

### **Step 1: Test Script**

Create test file:

```bash
cd ~/raspberry-pi
sudo nano test-dc-motor.py
```

Paste this code:

```python
#!/usr/bin/env python3
from gpiozero import Motor
from time import sleep
import sys

print("DC Motor Test")
print("=" * 40)

try:
    # Create motor (adjust pins if needed)
    motor = Motor(forward=23, backward=24, enable=18)

    print("Test 1: Forward (full speed)")
    motor.forward()
    sleep(3)

    print("Test 2: Stop")
    motor.stop()
    sleep(1)

    print("Test 3: Backward (full speed)")
    motor.backward()
    sleep(3)

    print("Test 4: Stop")
    motor.stop()
    sleep(1)

    print("Test 5: Speed control (0% → 100%)")
    for speed in [0.2, 0.4, 0.6, 0.8, 1.0]:
        print(f"  Speed: {speed*100}%")
        motor.forward(speed=speed)
        sleep(1)

    motor.stop()
    motor.close()

    print()
    print("✅ Test complete!")

except KeyboardInterrupt:
    motor.stop()
    motor.close()
    print("\nTest interrupted")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
```

Run it:
```bash
sudo python3 test-dc-motor.py
```

---

## 🎮 What Can You Control?

With a DC motor, you can make:

1. **Fan** - Speed controlled cooling fan
2. **Water pump** - For automated watering system
3. **Conveyor belt** - Small item transport
4. **Wheels** - For robot car (need 2 motors)
5. **Mixer** - Automated stirring
6. **Drill** - Small drilling tasks
7. **Turbine** - Wind simulation

**Note:** DC motors rotate continuously, not to specific positions like servos!

---

## 🔧 GPIO Pin Configuration

Currently in your `iot_client.py`, the servo is configured on GPIO18. For DC motor:

```python
# Remove or comment out servo config:
# "Servo Cửa": GPIODeviceConfig(...)

# Add DC motor config:
"Motor Quạt": GPIODeviceConfig(
    gpio_pin=23,  # IN1 (forward)
    name="Motor Quạt",
    device_type=DeviceType.MOTOR,  # New type needed!
),
```

**You'll need to add MOTOR device type to your code!**

---

## ⚠️ Safety Notes

1. **Always use motor driver** - Never connect motor directly to Pi!
2. **Common ground** - Pi GND and motor power GND must connect
3. **Correct voltage** - Check your motor's voltage rating
4. **Current limit** - L298N supports up to 2A per motor
5. **Flyback diode** - Always use diode to protect from voltage spikes
6. **Secure wiring** - Loose wires can cause short circuits

---

## 🛒 Shopping List

| Item | Price | Where |
|------|-------|-------|
| L298N Motor Driver | $2-3 | AliExpress, Amazon |
| DC Motor 3-6V | $1-2 | Electronics store |
| Power Supply 5-12V | $3-5 | Phone charger/adapter |
| Jumper Wires (F-F) | $1-2 | Electronics store |

**Total: ~$10 for complete setup**

---

## 📊 Motor Driver Comparison

| Feature | L298N | L9110S | Transistor |
|---------|-------|--------|------------|
| Price | $2-3 | $1-2 | $0.50 |
| Motors | 2 | 2 | 1 |
| Speed Control | ✅ Yes | ✅ Yes | ❌ No |
| Direction | ✅ Yes | ✅ Yes | ❌ No |
| Max Current | 2A | 800mA | Depends |
| Difficulty | Easy | Easy | Medium |

**Recommendation:** Get L298N for best features and ease of use!

---

## 🎯 Quick Start Checklist

- [ ] Buy L298N motor driver module
- [ ] Get external power supply (match motor voltage)
- [ ] Wire power supply to L298N
- [ ] Wire L298N to Raspberry Pi (GND + 3 control pins)
- [ ] Wire DC motor to L298N output
- [ ] Test with Python script
- [ ] Motor spins forward/backward
- [ ] Speed control works

---

## Need Help?

**Tell me:**
1. What voltage is your DC motor? (check label or measure)
2. Do you have a motor driver, or need to buy one?
3. What do you want to control with this motor?

I'll help you get it working! 🔧
