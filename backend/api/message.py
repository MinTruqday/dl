from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query, Request, WebSocket, HTTPException
from api.dependency import get_current_user
from core.config import settings
from models.user import UserInDB
from models.message import MessageCreate
import httpx
import websockets
import asyncio

CONTACT_URL = settings.CONTACT_SERVICE_URL
CONTACT_WS_URL = CONTACT_URL.replace("http://", "ws://").replace("https://", "wss://")

router = APIRouter(prefix='/tro-chuyen')

async def _proxy(method: str, path: str, **kwargs):
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            res = await client.request(method, f"{CONTACT_URL}{path}", **kwargs)
            if res.status_code >= 400:
                raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Lỗi liên lạc"))
            return res.json()
        except HTTPException:
            raise
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Không thể kết nối đến Contact Service: {e}")

@router.websocket('/ws/{user_id}')
async def websocket_proxy(websocket: WebSocket, user_id: str, token: str = Query(...)):
    await websocket.accept()
    try:
        async with websockets.connect(f"{CONTACT_WS_URL}/tro-chuyen/ws/{user_id}?token={token}") as target_ws:
            async def forward_client_to_target():
                try:
                    while True:
                        msg = await websocket.receive_text()
                        await target_ws.send(msg)
                except Exception:
                    pass

            async def forward_target_to_client():
                try:
                    while True:
                        msg = await target_ws.recv()
                        await websocket.send_text(msg)
                except Exception:
                    pass

            await asyncio.gather(
                forward_client_to_target(),
                forward_target_to_client()
            )
    except Exception:
        pass
    finally:
        try:
            await websocket.close()
        except:
            pass

@router.post('/tin-nhan', response_model=APIResponse[Any])
async def send_message(req: MessageCreate, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("POST", "/tro-chuyen/tin-nhan", json=req.model_dump(), headers={"X-User-Id": str(current_user.id)})

@router.get('/tin-nhan/{other_user_id}', response_model=APIResponse[Any])
async def get_messages(other_user_id: str, cursor: str = None, limit: int = Query(50), current_user: UserInDB = Depends(get_current_user)):
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
    return await _proxy("GET", f"/tro-chuyen/tin-nhan/{other_user_id}", params=params, headers={"X-User-Id": str(current_user.id)})

@router.get('/hoi-thoai', response_model=APIResponse[Any])
async def get_conversations(current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("GET", "/tro-chuyen/hoi-thoai", headers={"X-User-Id": str(current_user.id)})

@router.post('/ghim/{message_id}', response_model=APIResponse[Any])
async def toggle_pin(message_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("POST", f"/tro-chuyen/ghim/{message_id}", headers={"X-User-Id": str(current_user.id)})

@router.put('/chinh-sua/{message_id}', response_model=APIResponse[Any])
async def edit_message(message_id: str, req: dict, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("PUT", f"/tro-chuyen/chinh-sua/{message_id}", json=req, headers={"X-User-Id": str(current_user.id)})

@router.delete('/tin-nhan/{message_id}', response_model=APIResponse[Any])
async def recall_message(message_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("DELETE", f"/tro-chuyen/tin-nhan/{message_id}", headers={"X-User-Id": str(current_user.id)})

@router.get('/tim-kiem/{other_user_id}', response_model=APIResponse[Any])
async def search_messages(other_user_id: str, q: str = Query(...), current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("GET", f"/tro-chuyen/tim-kiem/{other_user_id}", params={"q": q}, headers={"X-User-Id": str(current_user.id)})

@router.post('/tin-nhan/{message_id}/cam-xuc', response_model=APIResponse[Any])
async def add_reaction(message_id: str, req: dict, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("POST", f"/tro-chuyen/tin-nhan/{message_id}/cam-xuc", json=req, headers={"X-User-Id": str(current_user.id)})

@router.post('/doc-tin-nhan/{other_user_id}', response_model=APIResponse[Any])
async def mark_as_read(other_user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("POST", f"/tro-chuyen/doc-tin-nhan/{other_user_id}", headers={"X-User-Id": str(current_user.id)})

@router.post('/chia-se-tai-lieu/{receiver_id}', response_model=APIResponse[Any])
async def share_document(receiver_id: str, req: dict, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("POST", f"/tro-chuyen/chia-se-tai-lieu/{receiver_id}", json=req, headers={"X-User-Id": str(current_user.id)})

@router.get('/tai-lieu-chia-se/{other_user_id}', response_model=APIResponse[Any])
async def get_shared_attachments(other_user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("GET", f"/tro-chuyen/tai-lieu-chia-se/{other_user_id}", headers={"X-User-Id": str(current_user.id)})

@router.post('/chan/{other_user_id}', response_model=APIResponse[Any])
async def block_user(other_user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("POST", f"/tro-chuyen/chan/{other_user_id}", headers={"X-User-Id": str(current_user.id)})

@router.post('/bo-chan/{other_user_id}', response_model=APIResponse[Any])
async def unblock_user(other_user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("POST", f"/tro-chuyen/bo-chan/{other_user_id}", headers={"X-User-Id": str(current_user.id)})

@router.get('/trang-thai-chan/{other_user_id}', response_model=APIResponse[Any])
async def get_blocked_status(other_user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("GET", f"/tro-chuyen/trang-thai-chan/{other_user_id}", headers={"X-User-Id": str(current_user.id)})

@router.post('/ghim-hoi-thoai/{other_user_id}', response_model=APIResponse[Any])
async def toggle_pin_conversation(other_user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("POST", f"/tro-chuyen/ghim-hoi-thoai/{other_user_id}", headers={"X-User-Id": str(current_user.id)})

@router.post('/dich/{message_id}', response_model=APIResponse[Any])
async def translate_message(message_id: str, req: dict, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("POST", f"/tro-chuyen/dich/{message_id}", json=req, headers={"X-User-Id": str(current_user.id)})

@router.post('/nhom', response_model=APIResponse[Any])
async def create_group(req: dict, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("POST", "/tro-chuyen/nhom", json=req, headers={"X-User-Id": str(current_user.id)})

@router.post('/nhap-tin-nhan/{other_user_id}', response_model=APIResponse[Any])
async def save_draft(other_user_id: str, req: dict, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("POST", f"/tro-chuyen/nhap-tin-nhan/{other_user_id}", json=req, headers={"X-User-Id": str(current_user.id)})

@router.get('/nhap-tin-nhan/{other_user_id}', response_model=APIResponse[Any])
async def get_draft(other_user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("GET", f"/tro-chuyen/nhap-tin-nhan/{other_user_id}", headers={"X-User-Id": str(current_user.id)})

@router.post('/tu-huy/{other_user_id}', response_model=APIResponse[Any])
async def toggle_self_destruct(other_user_id: str, req: dict, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("POST", f"/tro-chuyen/tu-huy/{other_user_id}", json=req, headers={"X-User-Id": str(current_user.id)})

@router.post('/tat-am/{other_user_id}', response_model=APIResponse[Any])
async def toggle_mute(other_user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("POST", f"/tro-chuyen/tat-am/{other_user_id}", headers={"X-User-Id": str(current_user.id)})

@router.get('/cai-dat/{other_user_id}', response_model=APIResponse[Any])
async def get_conversation_settings(other_user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("GET", f"/tro-chuyen/cai-dat/{other_user_id}", headers={"X-User-Id": str(current_user.id)})

@router.delete('/hoi-thoai/{other_user_id}', response_model=APIResponse[Any])
async def delete_conversation(other_user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("DELETE", f"/tro-chuyen/hoi-thoai/{other_user_id}", headers={"X-User-Id": str(current_user.id)})