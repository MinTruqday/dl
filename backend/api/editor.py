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

@router.post("/{document_id}/analyze-plagiarism")
async def analyze_internal_plagiarism(
    document_id: str,
    content_payload: dict,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    return await EditorService.analyze_internal_plagiarism(document_id, content_payload, current_user)

@router.post("/{document_id}/keystroke")
async def sync_keystroke_buffer(
    document_id: str,
    payload: dict,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    return await EditorService.sync_keystroke_buffer(document_id, payload, current_user)

@router.get("/latex")
async def get_latex():
    return await EditorService.get_latex()

@router.post("/author/documents/{document_id}/suggestions")
async def add_inline_suggestion(
    document_id: str, 
    payload: dict, 
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    return await EditorService.add_inline_suggestion(document_id, payload, current_user)

@router.put("/author/suggestions/{suggestion_id}/resolve")
async def resolve_suggestion(
    suggestion_id: str, 
    payload: dict, 
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    return await EditorService.resolve_suggestion(suggestion_id, payload, current_user)

@router.post("/author/pomodoro")
async def sync_pomodoro_session(
    payload: dict, 
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    return await EditorService.sync_pomodoro_session(payload, current_user)

@router.post("/{document_id}/auto-save")
async def auto_save_draft(document_id: str, content: dict, current_user: UserInDB = Depends(get_current_user)):
    return await EditorService.auto_save_draft(document_id, content, current_user)

@router.post("/{document_id}/submit-review")
async def submit_for_review(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await EditorService.submit_for_review(document_id, current_user)

@router.post("/{document_id}/plagiarism-check")
async def check_deep_plagiarism(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await EditorService.check_deep_plagiarism(document_id, current_user)

