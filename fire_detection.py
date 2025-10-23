"""Command line helper for running the fire detector on saved images."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the backend package is importable when running this script directly
BACKEND_DIR = Path(__file__).resolve().parent / "backend"
if BACKEND_DIR.exists() and str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.utils.fire_detection import FireDetector, FireParams

def main():
    import sys
    if len(sys.argv) < 2:
        print("Sử dụng: python fire_detection.py <ảnh.jpg>")
        return
    detector = FireDetector()
    result = detector.detect_from_path(sys.argv[1])

    print("=" * 50)
    print("KẾT QUẢ PHÁT HIỆN LỬA")
    print("=" * 50)
    print(f"Trạng thái: {'🔥 PHÁT HIỆN LỬA' if result['has_fire'] else '✅ KHÔNG CÓ LỬA'}")
    print(f"Độ tin cậy: {result['confidence']}%")
    print(f"Số vùng lửa: {result['fire_regions']}")
    print(f"Tổng diện tích lửa: {result['total_fire_area']} pixels")
    print(f"Phần trăm lửa: {result['fire_percentage']}%")
    print("=" * 50)

if __name__ == "__main__":
    main()
