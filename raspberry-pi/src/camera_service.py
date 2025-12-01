"""
Camera Service cho Raspberry Pi 5
Capture video từ USB webcam và gửi frames lên server
"""

import cv2
import base64
import logging
import threading
import time
from typing import Optional, Callable
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class CameraConfig:
    """Cấu hình camera"""
    device_index: int = 0  # /dev/video0
    width: int = 1280
    height: int = 720
    fps: int = 30
    capture_interval: float = 0.5  # Gửi frame mỗi 0.5 giây
    jpeg_quality: int = 75  # Chất lượng JPEG (0-100)
    max_dimension: int = 720  # Resize về max 720px


class CameraService:
    """
    Service để capture video từ USB webcam

    Capture frames định kỳ và gọi callback với JPEG base64
    """

    def __init__(self, config: CameraConfig, mock_mode: bool = False):
        """
        Args:
            config: CameraConfig object
            mock_mode: Nếu True, tạo frames giả (để test)
        """
        self.config = config
        self.mock_mode = mock_mode
        self.capture: Optional[cv2.VideoCapture] = None
        self.running = False
        self.capture_thread: Optional[threading.Thread] = None
        self.frame_callback: Optional[Callable[[str], None]] = None

    def initialize(self) -> bool:
        """
        Khởi tạo camera

        Returns:
            True nếu thành công
        """
        if self.mock_mode:
            logger.info("[MOCK] Camera khởi tạo ở chế độ mock")
            return True

        try:
            logger.info(f"Đang mở camera tại /dev/video{self.config.device_index}...")
            self.capture = cv2.VideoCapture(self.config.device_index)

            if not self.capture.isOpened():
                logger.error("Không thể mở camera")
                return False

            # Cấu hình độ phân giải
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
            self.capture.set(cv2.CAP_PROP_FPS, self.config.fps)

            # Đọc một frame test
            ret, frame = self.capture.read()
            if not ret:
                logger.error("Không thể đọc frame từ camera")
                return False

            actual_width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.capture.get(cv2.CAP_PROP_FPS))

            logger.info(
                f"Camera khởi tạo thành công: {actual_width}x{actual_height} @ {actual_fps}fps"
            )
            return True

        except Exception as e:
            logger.error(f"Lỗi khởi tạo camera: {e}")
            return False

    def set_frame_callback(self, callback: Callable[[str], None]) -> None:
        """
        Đăng ký callback để nhận frames

        Args:
            callback: Function nhận base64 JPEG string
        """
        self.frame_callback = callback

    def start_capture(self) -> bool:
        """
        Bắt đầu capture frames trong background thread

        Returns:
            True nếu thành công
        """
        if self.running:
            logger.warning("Camera đã đang chạy")
            return False

        self.running = True
        self.capture_thread = threading.Thread(
            target=self._capture_loop,
            daemon=True,
            name="CameraThread"
        )
        self.capture_thread.start()
        logger.info("Camera capture đã bắt đầu")
        return True

    def stop_capture(self) -> None:
        """Dừng capture"""
        if not self.running:
            return

        self.running = False
        if self.capture_thread is not None:
            self.capture_thread.join(timeout=2.0)
            logger.info("Camera capture đã dừng")

    def _capture_loop(self) -> None:
        """Main loop capture frames"""
        logger.info("Camera capture loop bắt đầu")

        frame_count = 0

        while self.running:
            try:
                if self.mock_mode:
                    # Tạo frame giả
                    jpeg_b64 = self._create_mock_frame()
                else:
                    # Capture frame thật
                    jpeg_b64 = self._capture_frame()

                # Gọi callback nếu có
                if jpeg_b64 and self.frame_callback:
                    frame_count += 1
                    # Log every 10th frame to avoid spam
                    if frame_count % 10 == 0:
                        logger.info(f"Đã gửi frame #{frame_count} ({len(jpeg_b64)} bytes)")
                    self.frame_callback(jpeg_b64)
                elif not jpeg_b64:
                    logger.warning("Frame capture thất bại")

                # Chờ theo interval
                time.sleep(self.config.capture_interval)

            except Exception as e:
                logger.error(f"Lỗi trong capture loop: {e}")
                time.sleep(1.0)

        logger.info(f"Camera capture loop kết thúc (total frames: {frame_count})")

    def _capture_frame(self) -> Optional[str]:
        """
        Capture một frame và encode sang JPEG base64

        Returns:
            Base64 encoded JPEG string hoặc None nếu lỗi
        """
        if self.capture is None:
            return None

        try:
            ret, frame = self.capture.read()
            if not ret:
                logger.warning("Không đọc được frame")
                return None

            # Resize nếu cần
            frame = self._resize_frame(frame)

            # Encode sang JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.config.jpeg_quality]
            ret, buffer = cv2.imencode('.jpg', frame, encode_param)

            if not ret:
                logger.warning("Không encode được frame sang JPEG")
                return None

            # Convert sang base64
            jpeg_bytes = buffer.tobytes()
            jpeg_b64 = base64.b64encode(jpeg_bytes).decode('utf-8')

            return jpeg_b64

        except Exception as e:
            logger.error(f"Lỗi capture frame: {e}")
            return None

    def _resize_frame(self, frame):
        """Resize frame về kích thước phù hợp"""
        height, width = frame.shape[:2]
        max_dim = self.config.max_dimension

        if width <= max_dim and height <= max_dim:
            return frame

        # Resize giữ nguyên tỷ lệ
        if width > height:
            new_width = max_dim
            new_height = int(height * (max_dim / width))
        else:
            new_height = max_dim
            new_width = int(width * (max_dim / height))

        resized = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
        return resized

    def _create_mock_frame(self) -> str:
        """Tạo một mock frame (ảnh đen có text)"""
        import numpy as np

        # Tạo ảnh đen
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Thêm text
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(
            frame,
            f"MOCK CAMERA - {timestamp}",
            (50, 240),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        # Encode sang JPEG
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.config.jpeg_quality]
        ret, buffer = cv2.imencode('.jpg', frame, encode_param)

        if ret:
            jpeg_bytes = buffer.tobytes()
            return base64.b64encode(jpeg_bytes).decode('utf-8')

        return ""

    def cleanup(self) -> None:
        """Dọn dẹp và release camera"""
        self.stop_capture()

        if self.capture is not None and not self.mock_mode:
            try:
                self.capture.release()
                logger.info("Camera đã được release")
            except Exception as e:
                logger.error(f"Lỗi khi release camera: {e}")

        self.capture = None
