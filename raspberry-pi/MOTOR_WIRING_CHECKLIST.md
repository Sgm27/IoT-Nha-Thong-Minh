# DC Motor Wiring Checklist - Step by Step

Quick reference guide for connecting your 2-wire DC motor with L298N driver.

## ⚠️ BEFORE YOU START

**CRITICAL SAFETY:**
- ❌ NEVER connect the motor directly to Raspberry Pi GPIO!
- ❌ This WILL destroy your Pi!
- ✅ You MUST use L298N motor driver module

---

## 📦 What You Need

- [ ] L298N Motor Driver Module (~$2-3)
- [ ] Your 2-wire DC motor
- [ ] External power supply (5V-12V, match your motor voltage)
- [ ] 7x Jumper wires (female-to-female)
- [ ] Raspberry Pi 5 (already have)

---

## 🔧 Step-by-Step Wiring

### Step 1: Identify L298N Pins

Look at your L298N module (blue PCB board):

```
L298N Top View:
┌─────────────────────────────┐
│  [12V] [GND] [5V]           │ ← Power input (top edge)
│                             │
│  [ENA] ← Jumper here!       │ ← Remove this jumper!
│  [IN1] [IN2]                │ ← Control pins
│                             │
│  [OUT1] [OUT2]              │ ← Motor output (screw terminals)
└─────────────────────────────┘
```

**IMPORTANT:** Remove the jumper on ENA pin before wiring!

---

### Step 2: Connect Power Supply to L298N

**First connection - Power:**

```
External Power Supply         L298N Module
┌──────────────────┐         ┌──────────┐
│                  │         │          │
│  (+) Positive ───┼────────→│  12V     │
│                  │         │          │
│  (-) Negative ───┼────────→│  GND     │
│                  │         │          │
└──────────────────┘         └──────────┘
```

**Wire colors:**
- Red wire → 12V (or 5V/6V/9V depending on your motor)
- Black wire → GND

---

### Step 3: Connect DC Motor to L298N

**Second connection - Motor:**

```
2-Wire DC Motor              L298N Module
┌──────────────────┐         ┌──────────┐
│                  │         │          │
│  Wire 1 (Any) ───┼────────→│  OUT1    │
│                  │         │          │
│  Wire 2 (Any) ───┼────────→│  OUT2    │
│                  │         │          │
└──────────────────┘         └──────────┘
```

**Note:** DC motor wires have no polarity - either wire can go to OUT1/OUT2.
If motor spins wrong direction, just swap the wires!

---

### Step 4: Connect L298N to Raspberry Pi

**Third connection - Control + Common Ground:**

```
L298N Module                 Raspberry Pi 5
┌──────────┐                 ┌──────────────┐
│          │                 │              │
│  GND  ───┼────────────────→│  Pin 6 (GND) │ ⚠️ CRITICAL!
│          │                 │              │
│  ENA  ───┼────────────────→│  Pin 12 (GPIO18) │
│          │                 │              │
│  IN1  ───┼────────────────→│  Pin 16 (GPIO23) │
│          │                 │              │
│  IN2  ───┼────────────────→│  Pin 18 (GPIO24) │
│          │                 │              │
└──────────┘                 └──────────────┘
```

**Pin mapping:**
1. L298N GND → Pi Pin 6 (GND) - **VERY IMPORTANT! Common ground!**
2. L298N ENA → Pi Pin 12 (GPIO18) - Speed control
3. L298N IN1 → Pi Pin 16 (GPIO23) - Direction control
4. L298N IN2 → Pi Pin 18 (GPIO24) - Direction control

---

## 📍 Raspberry Pi Pin Layout

```
Raspberry Pi 5 GPIO Header (looking from above, USB ports facing down):

     3.3V ●  ● 5V
          ●  ● 5V
          ●  ● GND  ← Pin 6 (L298N GND)
  GPIO14  ●  ● GPIO15
          ●  ● GPIO18 ← Pin 12 (L298N ENA)
          ●  ● GND
          ●  ● GPIO23 ← Pin 16 (L298N IN1)
   GPIO8  ●  ● GPIO24 ← Pin 18 (L298N IN2)
```

---

## ✅ Wiring Verification Checklist

Before powering on, verify:

- [ ] **Power supply connected to L298N:**
  - [ ] (+) → L298N 12V pin
  - [ ] (-) → L298N GND pin

- [ ] **DC motor connected to L298N:**
  - [ ] Motor wire 1 → L298N OUT1
  - [ ] Motor wire 2 → L298N OUT2

- [ ] **L298N connected to Pi:**
  - [ ] L298N GND → Pi Pin 6 (GND) ← **MUST HAVE COMMON GROUND!**
  - [ ] L298N ENA → Pi Pin 12 (GPIO18)
  - [ ] L298N IN1 → Pi Pin 16 (GPIO23)
  - [ ] L298N IN2 → Pi Pin 18 (GPIO24)

- [ ] **Jumper removed from L298N ENA pin**

- [ ] **No wires loose or touching each other**

---

## 🧪 Testing

Once wired, test with this command:

```bash
# SSH into your Pi
ssh pi@raspberrypi.local

# Navigate to project
cd ~/raspberry-pi

# Run test script
sudo python3 scripts/test-dc-motor.py
```

**Expected behavior:**
1. Motor spins forward (3 seconds)
2. Motor stops
3. Motor spins backward (3 seconds)
4. Motor stops
5. Motor gradually speeds up 20% → 100%
6. Test complete

**If motor doesn't move:**
- Check common ground (Pi GND to L298N GND)
- Check power supply is plugged in
- Verify jumper removed from ENA
- Try swapping motor wires at OUT1/OUT2

---

## 🎮 Interactive Testing

For manual control:

```bash
sudo python3 scripts/test-dc-motor.py --interactive
```

Commands:
- `f` - Forward full speed
- `b` - Backward full speed
- `s` - Stop
- `f50` - Forward 50% speed
- `b75` - Backward 75% speed
- `q` - Quit

---

## ⚡ Common Issues

### Issue 1: Motor doesn't move at all
**Fix:** Check common ground! L298N GND and Pi GND MUST be connected.

### Issue 2: Motor moves but very weak
**Fix:** Check external power supply voltage matches motor rating.

### Issue 3: Motor spins opposite direction
**Fix:** Swap the two motor wires at OUT1/OUT2 terminals.

### Issue 4: "Permission denied" error
**Fix:** Run with `sudo`: `sudo python3 scripts/test-dc-motor.py`

### Issue 5: Motor jitters or stutters
**Fix:** Tighten screw terminals on L298N, check for loose wires.

---

## 🛒 Where to Buy L298N

**Online:**
- AliExpress: ~$2 (2-3 weeks shipping)
- Amazon: ~$5-8 (fast shipping)
- Local electronics store: $3-5

**Search for:** "L298N motor driver module" or "L298N dual H-bridge"

---

## 📊 Complete Connection Summary

```
Power Supply (+) ──→ L298N 12V
Power Supply (-) ──→ L298N GND ──→ Pi Pin 6 (GND)

Motor Wire 1 ──→ L298N OUT1
Motor Wire 2 ──→ L298N OUT2

L298N ENA ──→ Pi Pin 12 (GPIO18)
L298N IN1 ──→ Pi Pin 16 (GPIO23)
L298N IN2 ──→ Pi Pin 18 (GPIO24)
```

**Total connections:** 7 wires
**Estimated time:** 10-15 minutes

---

## 🎯 Next Steps After Testing

Once the motor works:

1. **Add to IoT Client** - Integrate motor control into `iot_client.py`
2. **Voice Control** - Control via Gemini voice commands
3. **Web UI** - Add motor control to frontend
4. **Automation** - Auto-control based on fire detection or other sensors

---

Need help? Check the full guide: **DC_MOTOR_SETUP.md**
