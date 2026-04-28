from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from models.user import UserInDB, RoleEnum
from api.dependencies import require_role, get_current_user
from services.editor import EditorService, manager
from typing import List, Optional
from loguru import logger

router = APIRouter(prefix="/ws")

@router.websocket("/editor/{document_id}")
async def editor_websocket(websocket: WebSocket, document_id: str):
    try:
        await manager.connect(websocket, document_id)
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data.encode("utf-8"), document_id, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, document_id)
    except Exception as e:
        logger.error(f"WebSocket error in {document_id}: {e}")
        manager.disconnect(websocket, document_id)

@router.websocket("/crdt/{document_id}")
async def editor_crdt_websocket(websocket: WebSocket, document_id: str):
    try:
        await manager.connect(websocket, document_id)
        while True:
            data = await websocket.receive_bytes()
            await manager.broadcast(data, document_id, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, document_id)
    except Exception as e:
        logger.error(f"CRDT WebSocket error in {document_id}: {e}")
        manager.disconnect(websocket, document_id)

@router.post("/{document_id}/analyze-plagiarism", response_model=APIResponse[Any])
async def analyze_internal_plagiarism(
    document_id: str,
    content_payload: dict,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    return APIResponse(data=await EditorService.analyze_internal_plagiarism(document_id, content_payload, current_user), message="Phân tích đạo văn nội bộ thành công.", status=200)

@router.post("/{document_id}/keystroke", response_model=APIResponse[Any])
async def sync_keystroke_buffer(
    document_id: str,
    payload: dict,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    return APIResponse(data=await EditorService.sync_keystroke_buffer(document_id, payload, current_user), message="Đồng bộ bộ đệm gõ phím thành công.", status=200)

@router.get("/latex", response_model=APIResponse[Any])
async def get_latex():
    return APIResponse(data=await EditorService.get_latex(), message="Lấy mã nguồn LaTeX thành công.", status=200)

@router.post("/author/documents/{document_id}/suggestions", response_model=APIResponse[Any])
async def add_inline_suggestion(
    document_id: str, 
    payload: dict, 
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    return APIResponse(data=await EditorService.add_inline_suggestion(document_id, payload, current_user), message="Thêm gợi ý nội dòng thành công.", status=201)

@router.put("/author/suggestions/{suggestion_id}/resolve", response_model=APIResponse[Any])
async def resolve_suggestion(
    suggestion_id: str, 
    payload: dict, 
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    return APIResponse(data=await EditorService.resolve_suggestion(suggestion_id, payload, current_user), message="Xử lý gợi ý thành công.", status=200)

@router.post("/author/pomodoro", response_model=APIResponse[Any])
async def sync_pomodoro_session(
    payload: dict, 
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    return APIResponse(data=await EditorService.sync_pomodoro_session(payload, current_user), message="Đồng bộ phiên Pomodoro thành công.", status=200)

@router.post("/{document_id}/auto-save", response_model=APIResponse[Any])
async def auto_save_draft(document_id: str, content: dict, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await EditorService.auto_save_draft(document_id, content, current_user), message="Tự động lưu bản nháp thành công.", status=200)

@router.post("/{document_id}/submit-review", response_model=APIResponse[Any])
async def submit_for_review(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await EditorService.submit_for_review(document_id, current_user), message="Gửi tài liệu để xem xét thành công.", status=201)

@router.post("/{document_id}/plagiarism-check", response_model=APIResponse[Any])
async def check_deep_plagiarism(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await EditorService.check_deep_plagiarism(document_id, current_user), message="Kiểm tra đạo văn chuyên sâu thành công.", status=200)

