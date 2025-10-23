import cv2
import numpy as np
import os
from dataclasses import dataclass

@dataclass
class FireParams:
    # HSV ranges for fire-like colors (tight to cut false positives)
    lower_fire1: tuple = (0, 150, 150)
    upper_fire1: tuple = (15, 255, 255)
    lower_fire2: tuple = (16, 150, 150)
    upper_fire2: tuple = (30, 255, 255)
    min_area: int = 500
    brightness_threshold: int = 200
    min_confidence: float = 15.0
    kernel_size: int = 7
    texture_norm: float = 3000.0  # for variance normalization

class FireDetector:
    def __init__(self, params: FireParams | None = None):
        self.p = params or FireParams()
        self.kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (self.p.kernel_size, self.p.kernel_size)
        )

        # Convert tuples to np arrays once
        self.lower_fire1 = np.array(self.p.lower_fire1, dtype=np.uint8)
        self.upper_fire1 = np.array(self.p.upper_fire1, dtype=np.uint8)
        self.lower_fire2 = np.array(self.p.lower_fire2, dtype=np.uint8)
        self.upper_fire2 = np.array(self.p.upper_fire2, dtype=np.uint8)

    # --- simple region quality checks (return 0..1) ---
    @staticmethod
    def _texture_score(gray: np.ndarray, mask: np.ndarray, norm: float) -> float:
        if np.count_nonzero(mask) == 0:
            return 0.0
        var = float(np.var(gray[mask > 0]))
        return float(np.clip(var / max(norm, 1e-6), 0.0, 1.0))

    @staticmethod
    def _color_var_score(hsv: np.ndarray, mask: np.ndarray) -> float:
        if np.count_nonzero(mask) == 0:
            return 0.0
        h, s, _ = cv2.split(hsv)
        h_std = float(np.std(h[mask > 0])) if np.count_nonzero(mask) else 0.0
        s_std = float(np.std(s[mask > 0])) if np.count_nonzero(mask) else 0.0
        return float(np.clip((h_std + s_std) / 60.0, 0.0, 1.0))

    def detect(self, image_path: str) -> dict:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Không tìm thấy: {image_path}")

        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Không đọc được: {image_path}")

        # Keep texture -> light blur only
        blurred = cv2.GaussianBlur(image, (3, 3), 0)

        # Precompute color spaces once
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
        _, _, v = cv2.split(hsv)

        # Color masks (two tight bands) + brightness gate
        mask1 = cv2.inRange(hsv, self.lower_fire1, self.upper_fire1)
        mask2 = cv2.inRange(hsv, self.lower_fire2, self.upper_fire2)
        fire_mask = cv2.bitwise_or(mask1, mask2)
        bright_mask = (v >= self.p.brightness_threshold).astype(np.uint8) * 255
        combined_mask = cv2.bitwise_and(fire_mask, bright_mask)

        # Morphology: open -> close to denoise & connect
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, self.kernel, iterations=2)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, self.kernel)

        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter contours quickly by multiple shape heuristics
        fire_contours = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < self.p.min_area:
                continue

            x, y, w, h = cv2.boundingRect(c)
            if h == 0:
                continue
            ar = w / float(h)
            if not (0.4 <= ar <= 2.5):
                continue

            hull = cv2.convexHull(c)
            hull_area = cv2.contourArea(hull)
            solidity = (area / hull_area) if hull_area > 0 else 0.0
            if solidity >= 0.95:   # very solid -> likely object, not fire
                continue

            fire_contours.append(c)

        has_fire = len(fire_contours) > 0
        image_area = image.shape[0] * image.shape[1]
        total_area = sum(cv2.contourArea(c) for c in fire_contours) if has_fire else 0.0

        # Confidence from multiple cues
        if has_fire and image_area > 0:
            area_ratio = total_area / float(image_area)
            area_score = np.clip(area_ratio * 300.0, 0.0, 30.0)

            # Scale brightness above threshold into [0..30]
            if np.count_nonzero(combined_mask):
                avg_v = float(np.mean(v[combined_mask > 0]))
            else:
                avg_v = 0.0
            bright_scaled = (avg_v - self.p.brightness_threshold) / 55.0
            brightness_score = np.clip(bright_scaled * 30.0, 0.0, 30.0)

            texture_score = self._texture_score(gray, combined_mask, self.p.texture_norm) * 20.0
            color_score = self._color_var_score(hsv, combined_mask) * 20.0

            confidence = float(np.clip(area_score + brightness_score + texture_score + color_score, 0.0, 100.0))
            if confidence < self.p.min_confidence:
                has_fire, confidence, total_area = False, 0.0, 0.0
        else:
            confidence = 0.0

        return {
            "has_fire": has_fire,
            "confidence": round(confidence, 2),
            "fire_regions": len(fire_contours) if has_fire else 0,
            "total_fire_area": int(total_area) if has_fire else 0,
            "fire_percentage": round((total_area / image_area) * 100.0, 2) if has_fire and image_area > 0 else 0.0,
        }

def main():
    import sys
    if len(sys.argv) < 2:
        print("Sử dụng: python fire_detection.py <ảnh.jpg>")
        return
    detector = FireDetector()
    result = detector.detect(sys.argv[1])

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
