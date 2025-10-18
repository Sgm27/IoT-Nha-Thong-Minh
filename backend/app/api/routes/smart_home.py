from typing import List

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
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
    return MusicResponse(selected_song=selected)


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
