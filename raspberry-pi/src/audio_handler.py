"""
Audio Handler cho Raspberry Pi 5
Xử lý audio input (microphone) và output (speaker)
"""

import pyaudio
import base64
import logging
import threading
import queue
import wave
import io
import struct
from typing import Optional, Callable
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class AudioConfig:
    """Cấu hình audio"""
    sample_rate: int = 16000  # Gemini yêu cầu 16kHz
    channels: int = 1  # Mono
    chunk_size: int = 1600  # 100ms chunks tại 16kHz
    format: int = pyaudio.paInt16  # 16-bit PCM
    input_device_index: Optional[int] = None  # None = default microphone
    output_device_index: Optional[int] = None  # None = default speaker


class AudioHandler:
    """
    Handler cho audio I/O

    - Capture microphone → PCM16 base64 chunks
    - Playback audio từ PCM16 base64 chunks
    """

    def __init__(self, config: AudioConfig, mock_mode: bool = False):
        """
        Args:
            config: AudioConfig object
            mock_mode: Nếu True, không dùng hardware thật
        """
        self.config = config
        self.mock_mode = mock_mode
        self.audio: Optional[pyaudio.PyAudio] = None

        # Microphone recording
        self.recording = False
        self.record_stream: Optional[pyaudio.Stream] = None
        self.record_thread: Optional[threading.Thread] = None
        self.audio_callback: Optional[Callable[[str], None]] = None

        # Speaker playback
        self.playback_stream: Optional[pyaudio.Stream] = None
        self.playback_queue: queue.Queue = queue.Queue()
        self.playback_thread: Optional[threading.Thread] = None
        self.playing = False

    def initialize(self) -> bool:
        """
        Khởi tạo PyAudio

        Returns:
            True nếu thành công
        """
        if self.mock_mode:
            logger.info("[MOCK] Audio khởi tạo ở chế độ mock")
            return True

        try:
            self.audio = pyaudio.PyAudio()

            # Log available devices
            self._log_audio_devices()

            logger.info("PyAudio khởi tạo thành công")
            return True

        except Exception as e:
            logger.error(f"Lỗi khởi tạo PyAudio: {e}")
            return False

    def _log_audio_devices(self) -> None:
        """Log danh sách audio devices"""
        if self.audio is None:
            return

        try:
            device_count = self.audio.get_device_count()
            logger.info(f"Tìm thấy {device_count} audio devices:")

            for i in range(device_count):
                info = self.audio.get_device_info_by_index(i)
                logger.info(
                    f"  [{i}] {info['name']} - "
                    f"In:{info['maxInputChannels']} Out:{info['maxOutputChannels']}"
                )
        except Exception as e:
            logger.warning(f"Không thể liệt kê audio devices: {e}")

    def _has_output_device(self) -> bool:
        """
        Kiểm tra xem có output device (speaker) không

        Returns:
            True nếu có ít nhất 1 output device
        """
        if self.audio is None:
            return False

        try:
            device_count = self.audio.get_device_count()
            for i in range(device_count):
                info = self.audio.get_device_info_by_index(i)
                if info['maxOutputChannels'] > 0:
                    return True
            return False
        except Exception as e:
            logger.error(f"Lỗi khi kiểm tra output device: {e}")
            return False

    def set_audio_callback(self, callback: Callable[[str], None]) -> None:
        """
        Đăng ký callback để nhận audio chunks từ microphone

        Args:
            callback: Function nhận base64 PCM16 string
        """
        self.audio_callback = callback

    def start_recording(self) -> bool:
        """
        Bắt đầu ghi âm từ microphone

        Returns:
            True nếu thành công
        """
        if self.recording:
            logger.warning("Recording đã đang chạy")
            return False

        if self.mock_mode:
            logger.info("[MOCK] Bắt đầu recording")
            self.recording = True
            return True

        try:
            # Mở input stream
            self.record_stream = self.audio.open(
                format=self.config.format,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                input=True,
                input_device_index=self.config.input_device_index,
                frames_per_buffer=self.config.chunk_size,
            )

            self.recording = True

            # Start recording thread
            self.record_thread = threading.Thread(
                target=self._record_loop,
                daemon=True,
                name="RecordThread"
            )
            self.record_thread.start()

            logger.info("Microphone recording đã bắt đầu")
            return True

        except Exception as e:
            logger.error(f"Lỗi khi bắt đầu recording: {e}")
            return False

    def stop_recording(self) -> None:
        """Dừng recording"""
        if not self.recording:
            return

        self.recording = False

        if self.record_thread is not None:
            self.record_thread.join(timeout=2.0)

        if self.record_stream is not None and not self.mock_mode:
            try:
                self.record_stream.stop_stream()
                self.record_stream.close()
            except Exception as e:
                logger.error(f"Lỗi khi đóng record stream: {e}")

        self.record_stream = None
        logger.info("Microphone recording đã dừng")

    def _record_loop(self) -> None:
        """Main loop ghi âm"""
        logger.info("Record loop bắt đầu")

        while self.recording:
            try:
                if self.mock_mode:
                    # Mock: tạo silent audio
                    import time
                    time.sleep(0.1)
                    continue

                # Đọc audio chunk
                audio_data = self.record_stream.read(
                    self.config.chunk_size,
                    exception_on_overflow=False
                )

                # Encode sang base64
                audio_b64 = base64.b64encode(audio_data).decode('utf-8')

                # Gọi callback
                if self.audio_callback:
                    self.audio_callback(audio_b64)

            except Exception as e:
                logger.error(f"Lỗi trong record loop: {e}")
                break

        logger.info("Record loop kết thúc")

    def start_playback(self) -> bool:
        """
        Bắt đầu playback thread

        Returns:
            True nếu thành công
        """
        if self.playing:
            logger.warning("Playback đã đang chạy")
            return False

        if self.mock_mode:
            logger.info("[MOCK] Bắt đầu playback")
            self.playing = True
            return True

        try:
            # Kiểm tra xem có output device không
            if not self._has_output_device():
                logger.warning("⚠️  Không tìm thấy output audio device (speaker)")
                logger.warning("⚠️  Playback sẽ bị tắt - hệ thống vẫn hoạt động bình thường")
                # Chạy ở chế độ mock để không block các tính năng khác
                self.mock_mode = True
                self.playing = True
                return True

            # Mở output stream
            self.playback_stream = self.audio.open(
                format=self.config.format,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                output=True,
                output_device_index=self.config.output_device_index,
                frames_per_buffer=self.config.chunk_size,
            )

            self.playing = True

            # Start playback thread
            self.playback_thread = threading.Thread(
                target=self._playback_loop,
                daemon=True,
                name="PlaybackThread"
            )
            self.playback_thread.start()

            logger.info("Speaker playback đã bắt đầu")
            return True

        except Exception as e:
            logger.error(f"Lỗi khi bắt đầu playback: {e}")
            logger.warning("⚠️  Playback sẽ bị tắt - hệ thống vẫn hoạt động bình thường")
            # Fallback to mock mode
            self.mock_mode = True
            self.playing = True
            return True

    def stop_playback(self) -> None:
        """Dừng playback"""
        if not self.playing:
            return

        self.playing = False

        # Clear queue
        while not self.playback_queue.empty():
            try:
                self.playback_queue.get_nowait()
            except queue.Empty:
                break

        if self.playback_thread is not None:
            self.playback_thread.join(timeout=2.0)

        if self.playback_stream is not None and not self.mock_mode:
            try:
                self.playback_stream.stop_stream()
                self.playback_stream.close()
            except Exception as e:
                logger.error(f"Lỗi khi đóng playback stream: {e}")

        self.playback_stream = None
        logger.info("Speaker playback đã dừng")

    def play_audio_chunk(self, audio_b64: str, sample_rate: int = 16000) -> None:
        """
        Queue một audio chunk để phát

        Args:
            audio_b64: Base64 encoded PCM16 audio
            sample_rate: Sample rate của audio chunk
        """
        if not self.playing and not self.mock_mode:
            logger.warning("Playback chưa được start")
            return

        # Decode base64
        try:
            audio_data = base64.b64decode(audio_b64)

            # Resample nếu cần (nếu sample rate khác với config)
            if sample_rate != self.config.sample_rate:
                audio_data = self._resample_audio(audio_data, sample_rate, self.config.sample_rate)

            # Add to queue
            self.playback_queue.put(audio_data)

        except Exception as e:
            logger.error(f"Lỗi khi queue audio chunk: {e}")

    def _playback_loop(self) -> None:
        """Main loop phát audio"""
        logger.info("Playback loop bắt đầu")

        while self.playing:
            try:
                # Lấy audio chunk từ queue (timeout 0.1s)
                audio_data = self.playback_queue.get(timeout=0.1)

                if self.mock_mode:
                    continue

                # Phát audio
                self.playback_stream.write(audio_data)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Lỗi trong playback loop: {e}")
                break

        logger.info("Playback loop kết thúc")

    def _resample_audio(self, audio_data: bytes, from_rate: int, to_rate: int) -> bytes:
        """
        Resample audio data (simple linear interpolation)

        Args:
            audio_data: Raw PCM16 bytes
            from_rate: Source sample rate
            to_rate: Target sample rate

        Returns:
            Resampled audio bytes
        """
        # Convert bytes to samples
        samples = struct.unpack(f'<{len(audio_data)//2}h', audio_data)

        # Simple linear interpolation
        ratio = to_rate / from_rate
        new_length = int(len(samples) * ratio)
        resampled = []

        for i in range(new_length):
            src_index = i / ratio
            src_index_int = int(src_index)
            src_index_frac = src_index - src_index_int

            if src_index_int + 1 < len(samples):
                # Linear interpolation
                sample = samples[src_index_int] * (1 - src_index_frac) + \
                         samples[src_index_int + 1] * src_index_frac
            else:
                sample = samples[src_index_int]

            resampled.append(int(sample))

        # Convert back to bytes
        return struct.pack(f'<{len(resampled)}h', *resampled)

    def cleanup(self) -> None:
        """Dọn dẹp audio resources"""
        self.stop_recording()
        self.stop_playback()

        if self.audio is not None and not self.mock_mode:
            try:
                self.audio.terminate()
                logger.info("PyAudio terminated")
            except Exception as e:
                logger.error(f"Lỗi khi terminate PyAudio: {e}")

        self.audio = None
