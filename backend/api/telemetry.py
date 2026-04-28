from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, WebSocket, Depends
from api.dependencies import get_current_user
from services.telemetry import TelemetryService

router = APIRouter()

@router.websocket("/ws/telemetry/read/{document_id}/{chapter_idx}")
async def websocket_read_telemetry(websocket: WebSocket, document_id: str, chapter_idx: int):
    await TelemetryService.websocket_read_telemetry(websocket, document_id, chapter_idx)

@router.post("/telemetry/heatmap", response_model=APIResponse[Any])
async def record_reading_heatmap(payload: dict, current_user = Depends(get_current_user)):
    return APIResponse(data=await TelemetryService.record_reading_heatmap(payload, current_user), message="Ghi nhận bản đồ nhiệt (heatmap) đọc sách thành công.", status=200)

@router.post("/telemetry/scroll-speed", response_model=APIResponse[Any])
async def analyze_scroll_velocity(payload: dict, current_user = Depends(get_current_user)):
    return APIResponse(data=await TelemetryService.analyze_scroll_velocity(payload, current_user), message="Phân tích tốc độ cuộn trang thành công.", status=200)
