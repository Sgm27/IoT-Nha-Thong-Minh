#!/usr/bin/env python3
"""
Simple script to test if camera is working on Raspberry Pi
"""

import cv2
import sys
import time

def test_camera(device_index=0):
    """Test camera at device index"""

    print("=" * 50)
    print("  Camera Test Script")
    print("=" * 50)
    print()

    print(f"Testing camera at /dev/video{device_index}...")

    # Try to open camera
    cap = cv2.VideoCapture(device_index)

    if not cap.isOpened():
        print(f"❌ FAILED: Cannot open camera /dev/video{device_index}")
        print()
        print("Troubleshooting:")
        print("  1. Check if camera is plugged in")
        print("  2. Run: ls /dev/video*")
        print("  3. Try different device index (0, 1, 2, etc.)")
        return False

    print("✅ Camera opened successfully!")
    print()

    # Get camera properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    print(f"Camera properties:")
    print(f"  Resolution: {width}x{height}")
    print(f"  FPS: {fps}")
    print()

    # Try to capture a few frames
    print("Capturing 5 test frames...")
    success_count = 0

    for i in range(5):
        ret, frame = cap.read()

        if ret:
            print(f"  ✅ Frame {i+1}: OK ({frame.shape[1]}x{frame.shape[0]})")
            success_count += 1
        else:
            print(f"  ❌ Frame {i+1}: FAILED")

        time.sleep(0.1)

    cap.release()

    print()
    print("=" * 50)

    if success_count == 5:
        print("✅ SUCCESS: Camera is working perfectly!")
        print()
        print("Next steps:")
        print("  Run the IoT client:")
        print("    sudo ./venv/bin/python3 src/iot_client.py")
        return True
    else:
        print(f"⚠️  WARNING: Only {success_count}/5 frames captured")
        print("Camera may be unstable")
        return False


if __name__ == "__main__":
    device_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0

    success = test_camera(device_index)
    sys.exit(0 if success else 1)
