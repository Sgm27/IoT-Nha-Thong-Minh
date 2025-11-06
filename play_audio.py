"""
Script để phát âm thanh từ file base64
"""
import base64
import io
import wave
from pathlib import Path

try:
    # Thử import pygame (thư viện phổ biến để phát âm thanh)
    import pygame
    USE_PYGAME = True
except ImportError:
    USE_PYGAME = False
    try:
        # Nếu không có pygame, thử dùng pydub
        from pydub import AudioSegment
        from pydub.playback import play
        USE_PYDUB = True
    except ImportError:
        USE_PYDUB = False

def play_audio_from_base64(base64_file_path):
    """
    Đọc file base64 và phát âm thanh
    
    Args:
        base64_file_path: Đường dẫn đến file chứa dữ liệu base64
    """
    # Đọc file base64
    print(f"Đang đọc file: {base64_file_path}")
    with open(base64_file_path, 'r') as f:
        base64_data = f.read()
    
    # Giải mã base64
    print("Đang giải mã dữ liệu base64...")
    audio_data = base64.b64decode(base64_data)
    
    # Lưu tạm thành file WAV để phát
    temp_wav = "temp_audio.wav"
    print(f"Đang lưu file tạm: {temp_wav}")
    with open(temp_wav, 'wb') as f:
        f.write(audio_data)
    
    # Phát âm thanh
    if USE_PYGAME:
        print("Đang phát âm thanh bằng pygame...")
        pygame.mixer.init()
        pygame.mixer.music.load(temp_wav)
        pygame.mixer.music.play()
        
        # Đợi đến khi phát xong
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        
        print("Phát xong!")
        
    elif USE_PYDUB:
        print("Đang phát âm thanh bằng pydub...")
        audio = AudioSegment.from_wav(temp_wav)
        play(audio)
        print("Phát xong!")
        
    else:
        print("\nKhông tìm thấy thư viện phát âm thanh!")
        print("Vui lòng cài đặt một trong các thư viện sau:")
        print("  pip install pygame")
        print("  hoặc")
        print("  pip install pydub")
        print(f"\nFile âm thanh đã được giải mã và lưu tại: {temp_wav}")
        print("Bạn có thể mở file này bằng trình phát nhạc của Windows.")
    
    # Dọn dẹp file tạm (tùy chọn)
    # Path(temp_wav).unlink(missing_ok=True)

if __name__ == "__main__":
    # Đường dẫn đến file base64
    base64_file = r"e:\BTL\BTL-IoT\data\fire_alert_audio.b64"
    
    print("=" * 60)
    print("SCRIPT PHÁT ÂM THANH TỪ FILE BASE64")
    print("=" * 60)
    
    try:
        play_audio_from_base64(base64_file)
    except Exception as e:
        print(f"\nLỗi: {e}")
        print("\nKiểm tra lại đường dẫn file và thử lại.")
