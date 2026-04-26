from fastapi import APIRouter, WebSocket, Depends
from api.dependencies import get_current_user
from services.telemetry import TelemetryService

router = APIRouter()

@router.websocket("/ws/telemetry/read/{document_id}/{chapter_idx}")
async def websocket_read_telemetry(websocket: WebSocket, document_id: str, chapter_idx: int):
    await TelemetryService.websocket_read_telemetry(websocket, document_id, chapter_idx)

@router.post("/telemetry/heatmap")
async def record_reading_heatmap(payload: dict, current_user = Depends(get_current_user)):
    return await TelemetryService.record_reading_heatmap(payload, current_user)

@router.post("/telemetry/scroll-speed")
async def analyze_scroll_velocity(payload: dict, current_user = Depends(get_current_user)):
    return await TelemetryService.analyze_scroll_velocity(payload, current_user)
