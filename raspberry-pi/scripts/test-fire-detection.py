#!/usr/bin/env python3
"""
Test fire detection locally on Raspberry Pi
Shows what the camera sees and fire detection results in real-time
"""

import cv2
import sys
import time
import numpy as np
from pathlib import Path

# Add parent directory to path to import fire detection
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    # Try to import from backend (if available)
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))
    from app.utils.fire_detection import FireDetector, FireParams
    FIRE_DETECTOR_AVAILABLE = True
except ImportError:
    print("⚠️  Backend fire detection not available")
    print("   This script needs the backend fire_detection.py file")
    FIRE_DETECTOR_AVAILABLE = False


def test_fire_detection_realtime(device_index=0, show_preview=False):
    """
    Test fire detection in real-time with camera feed

    Args:
        device_index: Camera device index (default 0 = /dev/video0)
        show_preview: Show OpenCV window with visualization (requires X11/display)
    """

    if not FIRE_DETECTOR_AVAILABLE:
        print("❌ Fire detector not available. Exiting.")
        return False

    print("=" * 60)
    print("  Fire Detection Test - Real-time Mode")
    print("=" * 60)
    print()

    # Initialize camera
    print(f"Opening camera /dev/video{device_index}...")
    cap = cv2.VideoCapture(device_index)

    if not cap.isOpened():
        print(f"❌ Cannot open camera /dev/video{device_index}")
        return False

    print("✅ Camera opened successfully")
    print()

    # Initialize fire detector
    print("Initializing fire detector...")
    detector = FireDetector()
    print(f"✅ Fire detector initialized")
    print(f"   HSV range: {detector.params.lower_hsv} - {detector.params.upper_hsv}")
    print(f"   Min contour area: {detector.params.min_contour_area}")
    print(f"   Fire threshold: {detector.params.fire_percentage_threshold * 100}%")
    print()

    print("=" * 60)
    print("Testing fire detection...")
    print()
    print("Instructions:")
    print("  1. Hold a lighter/candle in front of the camera")
    print("  2. Move it around to test detection")
    print("  3. Watch the detection results below")
    print("  4. Press Ctrl+C to stop")
    print()
    print("⚠️  SAFETY: Use small flame, keep fire extinguisher nearby!")
    print("=" * 60)
    print()

    frame_count = 0
    fire_detected_count = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Failed to read frame")
                break

            frame_count += 1

            # Detect fire
            result = detector.detect_fire(frame)

            # Print result every frame
            timestamp = time.strftime("%H:%M:%S")

            if result.fire_detected:
                fire_detected_count += 1
                print(f"🔥 [{timestamp}] FIRE DETECTED! "
                      f"Confidence: {result.confidence:.2f}, "
                      f"Fire%: {result.fire_percentage*100:.1f}%, "
                      f"Regions: {result.region_count}")

                # Visual feedback
                print("   🚨 🚨 🚨 ALARM! 🚨 🚨 🚨")
            else:
                # Only print every 10 frames to reduce spam
                if frame_count % 10 == 0:
                    print(f"✓ [{timestamp}] No fire detected "
                          f"(Fire%: {result.fire_percentage*100:.1f}%, "
                          f"Regions: {result.region_count})")

            # Show preview if requested (requires display)
            if show_preview:
                # Draw detection result on frame
                if result.fire_detected:
                    cv2.putText(frame, "FIRE DETECTED!", (50, 50),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                cv2.putText(frame, f"Fire: {result.fire_percentage*100:.1f}%",
                           (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                cv2.imshow("Fire Detection Test", frame)

                # Press 'q' to quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            time.sleep(0.1)  # ~10 FPS

    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("Test stopped by user")

    finally:
        cap.release()
        if show_preview:
            cv2.destroyAllWindows()

    print()
    print("=" * 60)
    print("Test Results:")
    print(f"  Total frames: {frame_count}")
    print(f"  Fire detected: {fire_detected_count} frames")
    if frame_count > 0:
        print(f"  Detection rate: {fire_detected_count/frame_count*100:.1f}%")
    print("=" * 60)

    return True


def test_fire_detection_single_frame(device_index=0):
    """Test fire detection on a single frame and show detailed analysis"""

    if not FIRE_DETECTOR_AVAILABLE:
        print("❌ Fire detector not available. Exiting.")
        return False

    print("=" * 60)
    print("  Fire Detection Test - Single Frame Analysis")
    print("=" * 60)
    print()

    # Initialize camera
    print(f"Opening camera /dev/video{device_index}...")
    cap = cv2.VideoCapture(device_index)

    if not cap.isOpened():
        print(f"❌ Cannot open camera /dev/video{device_index}")
        return False

    print("✅ Camera opened")
    print()
    print("Position your camera to show the test subject...")
    print("Press Enter when ready to capture...")
    input()

    # Capture frame
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("❌ Failed to capture frame")
        return False

    print("✅ Frame captured")
    print()

    # Initialize detector and analyze
    detector = FireDetector()
    result = detector.detect_fire(frame)

    # Print detailed results
    print("=" * 60)
    print("Detection Results:")
    print("=" * 60)
    print(f"Fire Detected: {'🔥 YES' if result.fire_detected else '✓ NO'}")
    print(f"Confidence: {result.confidence:.3f}")
    print(f"Fire Percentage: {result.fire_percentage*100:.2f}%")
    print(f"Fire Pixel Count: {result.fire_pixel_count}")
    print(f"Region Count: {result.region_count}")
    print()
    print("Detector Parameters:")
    print(f"  HSV Lower: {detector.params.lower_hsv}")
    print(f"  HSV Upper: {detector.params.upper_hsv}")
    print(f"  Min Contour Area: {detector.params.min_contour_area}")
    print(f"  Fire Threshold: {detector.params.fire_percentage_threshold*100}%")
    print("=" * 60)

    # Save frame for inspection
    output_file = "/tmp/fire_detection_test.jpg"
    cv2.imwrite(output_file, frame)
    print(f"Frame saved to: {output_file}")

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test fire detection")
    parser.add_argument("--device", type=int, default=0, help="Camera device index (default: 0)")
    parser.add_argument("--mode", choices=["realtime", "single"], default="realtime",
                       help="Test mode: realtime or single frame")
    parser.add_argument("--preview", action="store_true", help="Show OpenCV preview window")

    args = parser.parse_args()

    if args.mode == "realtime":
        success = test_fire_detection_realtime(args.device, args.preview)
    else:
        success = test_fire_detection_single_frame(args.device)

    sys.exit(0 if success else 1)
