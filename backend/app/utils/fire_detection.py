"""Computer-vision based fire detection helpers used by the backend services."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import cv2
import numpy as np


@dataclass(slots=True)
class FireParams:
    """Thresholds and heuristics controlling the fire detector."""

    lower_fire1: tuple[int, int, int] = (0, 150, 150)
    upper_fire1: tuple[int, int, int] = (15, 255, 255)
    lower_fire2: tuple[int, int, int] = (16, 150, 150)
    upper_fire2: tuple[int, int, int] = (30, 255, 255)
    min_area: int = 500
    brightness_threshold: int = 200
    min_confidence: float = 15.0
    kernel_size: int = 7
    texture_norm: float = 3000.0


class FireDetector:
    """Heuristic fire detector operating in the HSV colour space."""

    def __init__(self, params: Optional[FireParams] = None) -> None:
        self.p = params or FireParams()
        self.kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (self.p.kernel_size, self.p.kernel_size)
        )

        self.lower_fire1 = np.array(self.p.lower_fire1, dtype=np.uint8)
        self.upper_fire1 = np.array(self.p.upper_fire1, dtype=np.uint8)
        self.lower_fire2 = np.array(self.p.lower_fire2, dtype=np.uint8)
        self.upper_fire2 = np.array(self.p.upper_fire2, dtype=np.uint8)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def detect_from_path(self, image_path: str | os.PathLike[str]) -> Dict[str, float | int | bool]:
        """Run the detector on an image stored on disk."""

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy: {image_path}")

        image = cv2.imread(str(path))
        if image is None:
            raise ValueError(f"Không đọc được: {image_path}")
        return self._detect_from_image(image)

    # Backwards compatibility with the original CLI helper
    def detect(self, image_path: str | os.PathLike[str]) -> Dict[str, float | int | bool]:
        return self.detect_from_path(image_path)

    def detect_from_bytes(self, data: bytes) -> Dict[str, float | int | bool]:
        """Decode an image from bytes and run the detector."""

        if not data:
            raise ValueError("Không có dữ liệu ảnh để xử lý")

        array = np.frombuffer(data, dtype=np.uint8)
        image = cv2.imdecode(array, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Không thể giải mã dữ liệu ảnh")
        return self._detect_from_image(image)

    async def detect_from_bytes_async(self, data: bytes) -> Dict[str, float | int | bool]:
        """Asynchronous helper for running the detector in a thread."""

        return await asyncio.to_thread(self.detect_from_bytes, data)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _detect_from_image(self, image: np.ndarray) -> Dict[str, float | int | bool]:
        blurred = cv2.GaussianBlur(image, (3, 3), 0)

        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
        _, _, v = cv2.split(hsv)

        mask1 = cv2.inRange(hsv, self.lower_fire1, self.upper_fire1)
        mask2 = cv2.inRange(hsv, self.lower_fire2, self.upper_fire2)
        fire_mask = cv2.bitwise_or(mask1, mask2)
        bright_mask = (v >= self.p.brightness_threshold).astype(np.uint8) * 255
        combined_mask = cv2.bitwise_and(fire_mask, bright_mask)

        combined_mask = cv2.morphologyEx(
            combined_mask, cv2.MORPH_OPEN, self.kernel, iterations=2
        )
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, self.kernel)

        contours, _ = cv2.findContours(
            combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        fire_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.p.min_area:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            if h == 0:
                continue
            aspect_ratio = w / float(h)
            if not (0.4 <= aspect_ratio <= 2.5):
                continue

            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            solidity = (area / hull_area) if hull_area > 0 else 0.0
            if solidity >= 0.95:
                continue

            fire_contours.append(contour)

        has_fire = len(fire_contours) > 0
        image_area = image.shape[0] * image.shape[1]
        total_area = (
            sum(cv2.contourArea(contour) for contour in fire_contours)
            if has_fire
            else 0.0
        )

        if has_fire and image_area > 0:
            area_ratio = total_area / float(image_area)
            area_score = np.clip(area_ratio * 300.0, 0.0, 30.0)

            if np.count_nonzero(combined_mask):
                avg_v = float(np.mean(v[combined_mask > 0]))
            else:
                avg_v = 0.0
            bright_scaled = (avg_v - self.p.brightness_threshold) / 55.0
            brightness_score = np.clip(bright_scaled * 30.0, 0.0, 30.0)

            texture_score = (
                self._texture_score(gray, combined_mask, self.p.texture_norm) * 20.0
            )
            color_score = self._color_var_score(hsv, combined_mask) * 20.0

            confidence = float(
                np.clip(
                    area_score + brightness_score + texture_score + color_score,
                    0.0,
                    100.0,
                )
            )
            if confidence < self.p.min_confidence:
                has_fire, confidence, total_area = False, 0.0, 0.0
        else:
            confidence = 0.0

        return {
            "has_fire": has_fire,
            "confidence": round(confidence, 2),
            "fire_regions": len(fire_contours) if has_fire else 0,
            "total_fire_area": int(total_area) if has_fire else 0,
            "fire_percentage": round(
                (total_area / image_area) * 100.0, 2
            )
            if has_fire and image_area > 0
            else 0.0,
        }

    @staticmethod
    def _texture_score(gray: np.ndarray, mask: np.ndarray, norm: float) -> float:
        if np.count_nonzero(mask) == 0:
            return 0.0
        variance = float(np.var(gray[mask > 0]))
        return float(np.clip(variance / max(norm, 1e-6), 0.0, 1.0))

    @staticmethod
    def _color_var_score(hsv: np.ndarray, mask: np.ndarray) -> float:
        if np.count_nonzero(mask) == 0:
            return 0.0
        hue, saturation, _ = cv2.split(hsv)
        hue_std = float(np.std(hue[mask > 0])) if np.count_nonzero(mask) else 0.0
        sat_std = float(np.std(saturation[mask > 0])) if np.count_nonzero(mask) else 0.0
        return float(np.clip((hue_std + sat_std) / 60.0, 0.0, 1.0))


__all__ = ["FireDetector", "FireParams"]

