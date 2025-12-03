import os
import json
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

FACEPP_API_KEY = "fqM86YnEV7ZnFRDJYozeezYCIEbMnUxX"
FACEPP_API_SECRET = "p0fybge5pLxjHXXadlbxa9T9-P03Pp9B"

# Endpoint Face++ Compare API
FACEPP_COMPARE_URL = "https://api-us.faceplusplus.com/facepp/v3/compare"


def compare_faces(image1_path: str, image2_path: str, threshold: float = 80.0):
    """
    So sánh hai ảnh khuôn mặt bằng Face++.
    threshold: ngưỡng confidence (0–100) để coi là 'cùng người'.
    Trả về (confidence, is_same_person, raw_response_dict)
    """
    if not FACEPP_API_KEY or not FACEPP_API_SECRET:
        raise RuntimeError("Chưa cấu hình FACEPP_API_KEY / FACEPP_API_SECRET trong .env")

    data = {
        "api_key": FACEPP_API_KEY,
        "api_secret": FACEPP_API_SECRET,
    }

    # Gửi 2 file ảnh lên (multipart/form-data)
    with open(image1_path, "rb") as f1, open(image2_path, "rb") as f2:
        files = {
            "image_file1": f1,
            "image_file2": f2,
        }
        resp = requests.post(
            FACEPP_COMPARE_URL,
            data=data,
            files=files,
            timeout=15,
        )

    # Nếu HTTP lỗi -> raise để biết
    resp.raise_for_status()
    result = resp.json()

    # Face++ trả về trường 'confidence' (0–100)
    confidence = float(result.get("confidence", 0.0))
    is_same = confidence >= threshold

    print("===== Face++ Compare Result =====")
    print(f"Confidence: {confidence:.2f}")
    print(f"Same person (threshold {threshold}): {is_same}")
    print("Raw response:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    return confidence, is_same, result


if __name__ == "__main__":
    # Đổi thành đường dẫn ảnh thật của bạn
    img1 = "./backend/data/host/ducson.png"    # ảnh khuôn mặt chuẩn (user gốc)
    img2 = "./backend/data/images/capture_20251203T174325_236615.jpg"  # ảnh vừa chụp / cần xác thực

    compare_faces(img1, img2, threshold=80.0)
