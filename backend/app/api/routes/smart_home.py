from typing import List

from mimetypes import guess_type
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel, constr

from app.services.smart_home_service import LightState, get_smart_home_service


router = APIRouter(prefix="/smart-home", tags=["smart-home"])

smart_home_service = get_smart_home_service()


class LightRequest(BaseModel):
    location: constr(strip_whitespace=True, min_length=1)


class LightResponse(BaseModel):
    location: str
    is_on: bool


class MusicRequest(BaseModel):
    title: constr(strip_whitespace=True, min_length=1)


class MusicResponse(BaseModel):
    selected_song: str
    stream_url: str


def _serialize_light(state: LightState) -> dict:
    return {"location": state.location, "is_on": state.is_on}


@router.get("/lights", response_model=List[LightResponse])
def list_lights() -> List[LightResponse]:
    return [LightResponse(**_serialize_light(state)) for state in smart_home_service.get_lights()]


@router.get("/lights/{location}", response_model=LightResponse)
def get_light(location: str) -> LightResponse:
    state = smart_home_service.lighting_service.get_light_state(location)
    return LightResponse(**_serialize_light(state))


@router.post("/lights/on", response_model=LightResponse)
def turn_on_light(payload: LightRequest) -> LightResponse:
    state = smart_home_service.turn_on_light(payload.location)
    return LightResponse(**_serialize_light(state))


@router.post("/lights/off", response_model=LightResponse)
def turn_off_light(payload: LightRequest) -> LightResponse:
    state = smart_home_service.turn_off_light(payload.location)
    return LightResponse(**_serialize_light(state))


@router.get("/music/library", response_model=List[str])
def list_music_library() -> List[str]:
    return smart_home_service.list_music()


@router.post("/music/play", response_model=MusicResponse)
def play_music(payload: MusicRequest) -> MusicResponse:
    selected = smart_home_service.play_music(payload.title)
    if not selected:
        raise HTTPException(status_code=404, detail="Không tìm được bài hát phù hợp")
    file_path = smart_home_service.get_song_file(selected)
    if not file_path:
        raise HTTPException(status_code=404, detail="Không tìm được file bài hát phù hợp")
    query = urlencode({"title": selected})
    stream_url = f"/smart-home/music/stream?{query}"
    return MusicResponse(selected_song=selected, stream_url=stream_url)


@router.get("/music/stream")
def stream_music(title: str) -> FileResponse:
    file_path = smart_home_service.get_song_file(title)
    if not file_path:
        raise HTTPException(status_code=404, detail="Không tìm được file bài hát phù hợp")
    media_type, _ = guess_type(file_path.name)
    return FileResponse(file_path, media_type=media_type or "audio/mpeg", filename=file_path.name)


@router.websocket("/lights/stream")
async def stream_light_updates(websocket: WebSocket) -> None:
    await websocket.accept()
    queue = await smart_home_service.lighting_service.add_listener()
    try:
        while True:
            message = await queue.get()
            await websocket.send_json(message)
    except WebSocketDisconnect:
        pass
    finally:
        smart_home_service.lighting_service.remove_listener(queue)
