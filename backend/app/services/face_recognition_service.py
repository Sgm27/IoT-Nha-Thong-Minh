"""Service for face recognition using Face++ API."""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional, Tuple

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

# Thread pool for blocking HTTP requests
_executor = ThreadPoolExecutor(max_workers=2)


class FaceRecognitionService:
    """Compares captured faces against known host faces using Face++ API."""

    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        compare_url: Optional[str] = None,
        host_faces_dir: Optional[Path] = None,
        threshold: Optional[float] = None,
    ) -> None:
        self.api_key = api_key or settings.facepp_api_key
        self.api_secret = api_secret or settings.facepp_api_secret
        self.compare_url = compare_url or settings.facepp_compare_url
        self.host_faces_dir = host_faces_dir or settings.host_faces_directory
        self.threshold = threshold if threshold is not None else settings.face_recognition_threshold

        # Ensure host faces directory exists
        self.host_faces_dir.mkdir(parents=True, exist_ok=True)

        self._enabled = bool(self.api_key and self.api_secret)
        if not self._enabled:
            logger.warning(
                "Face++ API credentials not configured. "
                "Set FACEPP_API_KEY and FACEPP_API_SECRET in .env to enable face recognition."
            )

    @property
    def is_enabled(self) -> bool:
        """Check if face recognition is enabled and configured."""
        return self._enabled and settings.face_recognition_enabled

    def get_host_face_images(self) -> List[Path]:
        """Get all host face images from the host directory."""
        if not self.host_faces_dir.exists():
            return []

        images = []
        for ext in self.SUPPORTED_EXTENSIONS:
            images.extend(self.host_faces_dir.glob(f"*{ext}"))
            images.extend(self.host_faces_dir.glob(f"*{ext.upper()}"))
        return sorted(images)

    def _compare_faces_sync(
        self, image_data: bytes, host_image_path: Path
    ) -> Tuple[float, bool, Optional[dict]]:
        """
        Compare captured image bytes with a host image file using Face++ API.

        Returns:
            Tuple of (confidence, is_same_person, raw_response)
        """
        if not self.api_key or not self.api_secret:
            logger.error("Face++ API credentials not configured")
            return 0.0, False, None

        data = {
            "api_key": self.api_key,
            "api_secret": self.api_secret,
        }

        try:
            with open(host_image_path, "rb") as host_file:
                files = {
                    "image_file1": ("captured.jpg", image_data, "image/jpeg"),
                    "image_file2": host_file,
                }
                resp = requests.post(
                    self.compare_url,
                    data=data,
                    files=files,
                    timeout=15,
                )

            resp.raise_for_status()
            result = resp.json()

            # Check for Face++ API errors
            if "error_message" in result:
                logger.warning(
                    "Face++ API error for %s: %s",
                    host_image_path.name,
                    result.get("error_message"),
                )
                return 0.0, False, result

            confidence = float(result.get("confidence", 0.0))
            is_same = confidence >= self.threshold

            return confidence, is_same, result

        except requests.exceptions.Timeout:
            logger.error("Face++ API timeout comparing with %s", host_image_path.name)
            return 0.0, False, None
        except requests.exceptions.RequestException as e:
            logger.error("Face++ API request failed for %s: %s", host_image_path.name, e)
            return 0.0, False, None
        except Exception as e:
            logger.exception("Unexpected error comparing faces with %s: %s", host_image_path.name, e)
            return 0.0, False, None

    async def compare_with_host_faces(
        self, image_data: bytes
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Compare captured image with all host face images.

        Returns:
            Tuple of (is_host_detected, highest_confidence, matched_host_name)
        """
        if not self.is_enabled:
            logger.debug("Face recognition is disabled or not configured")
            return False, 0.0, None

        host_images = self.get_host_face_images()
        if not host_images:
            logger.warning("No host face images found in %s", self.host_faces_dir)
            return False, 0.0, None

        logger.info(
            "Comparing captured face with %d host image(s)...",
            len(host_images),
        )

        highest_confidence = 0.0
        matched_host: Optional[str] = None
        is_host_detected = False

        loop = asyncio.get_event_loop()

        for host_image in host_images:
            try:
                confidence, is_same, _ = await loop.run_in_executor(
                    _executor,
                    self._compare_faces_sync,
                    image_data,
                    host_image,
                )

                logger.info(
                    "Face++ compare result: %s -> confidence=%.2f%%, match=%s",
                    host_image.name,
                    confidence,
                    is_same,
                )

                if confidence > highest_confidence:
                    highest_confidence = confidence

                if is_same:
                    is_host_detected = True
                    matched_host = host_image.stem  # filename without extension
                    # Found a match, log immediately and stop checking
                    logger.info(
                        "========================================"
                    )
                    logger.info(
                        "HOST FACE DETECTED! Matched: %s (confidence: %.2f%%)",
                        matched_host,
                        confidence,
                    )
                    logger.info(
                        "========================================"
                    )
                    break

            except Exception as e:
                logger.exception(
                    "Error comparing with host image %s: %s",
                    host_image.name,
                    e,
                )

        if not is_host_detected:
            logger.warning(
                "========================================"
            )
            logger.warning(
                "DIFFERENT FACE DETECTED! Highest confidence: %.2f%% (threshold: %.2f%%)",
                highest_confidence,
                self.threshold,
            )
            logger.warning(
                "========================================"
            )

        return is_host_detected, highest_confidence, matched_host

    async def process_image(self, image_data: bytes) -> dict:
        """
        Process a captured image for face recognition.

        Returns:
            Dictionary with recognition results
        """
        is_host, confidence, matched_host = await self.compare_with_host_faces(image_data)

        return {
            "is_host_detected": is_host,
            "confidence": confidence,
            "matched_host": matched_host,
            "threshold": self.threshold,
        }


# Singleton instance
_face_recognition_service: Optional[FaceRecognitionService] = None


def get_face_recognition_service() -> FaceRecognitionService:
    """Get or create the face recognition service singleton."""
    global _face_recognition_service
    if _face_recognition_service is None:
        _face_recognition_service = FaceRecognitionService()
    return _face_recognition_service


__all__ = ["FaceRecognitionService", "get_face_recognition_service"]
