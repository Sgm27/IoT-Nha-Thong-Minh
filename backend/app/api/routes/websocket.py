from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.gemini_service import GeminiService


router = APIRouter()

gemini_service = GeminiService()


@router.websocket("/ws/gemini")
async def gemini_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        await gemini_service.handle_websocket_connection(websocket)
    except WebSocketDisconnect:
        raise
