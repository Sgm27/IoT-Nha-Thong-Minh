from datetime import datetime
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, constr

from app.services.smart_home_service import get_smart_home_service


router = APIRouter(prefix="/assistant", tags=["assistant"])

smart_home_service = get_smart_home_service()


class ChatRequest(BaseModel):
    message: constr(strip_whitespace=True, min_length=1)


class ChatResponse(BaseModel):
    reply: str
    timestamp: datetime
    suggestions: List[str] = []


@router.post("/chat", response_model=ChatResponse)
def chat_with_assistant(payload: ChatRequest) -> ChatResponse:
    message = payload.message.strip()
    normalized = message.lower()
    suggestions: List[str] = []

    if "đèn" in normalized:
        lights = smart_home_service.get_lights()
        if any(light.is_on for light in lights):
            reply = "Các đèn đang bật gồm: " + ", ".join(
                light.location for light in lights if light.is_on
            )
        else:
            reply = "Hiện tại tất cả đèn đều đang tắt. Bạn muốn bật đèn ở vị trí nào?"
        suggestions.append("Mở tab Điều khiển đèn để thao tác ngay.")
    elif "nhạc" in normalized or "bài hát" in normalized:
        music_state = smart_home_service.get_music_playback_state()
        if music_state.matched_song:
            reply = (
                "Đang phát bài {song} ở trạng thái {status}."
            ).format(
                song=music_state.matched_song,
                status="tạm dừng" if music_state.status == "paused" else "đang phát",
            )
        else:
            library = smart_home_service.list_music()
            if library:
                reply = "Bạn có thể yêu cầu các bài hát như: " + ", ".join(library[:5])
            else:
                reply = "Thư viện nhạc đang trống, hãy thêm file vào máy chủ để nghe nhé."
        suggestions.append("Chuyển sang tab Phát nhạc để xem danh sách bài hát.")
    else:
        reply = (
            "Xin chào! Tôi là trợ lý nhà thông minh. Bạn có thể hỏi tôi về việc bật/tắt đèn, "
            "phát nhạc hoặc những tính năng khác của ngôi nhà."
        )
        suggestions.extend(
            [
                "Nói 'Bật đèn phòng khách' để điều khiển đèn.",
                "Nói 'Phát bài hát [tên bài]' để nghe nhạc.",
            ]
        )

    return ChatResponse(reply=reply, timestamp=datetime.utcnow(), suggestions=suggestions)
