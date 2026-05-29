from typing import Any, List
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from api.dependency import get_current_user
from models.user import UserInDB
from models.chat import MessageCreate, MessageResponse, ConversationResponse
from services.chat import ChatService
from core.database import db_client
import json
import asyncio

router = APIRouter(prefix="/tro-chuyen")

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        asyncio.create_task(self._listen_redis(user_id, websocket))

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def _listen_redis(self, user_id: str, websocket: WebSocket):
        if not db_client.redis:
            return
            
        pubsub = db_client.redis.pubsub()
        channel_name = f"chat_delivery:{user_id}"
        await pubsub.subscribe(channel_name)
        
        try:
            while user_id in self.active_connections:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    await websocket.send_text(message["data"].decode("utf-8"))
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.warning(f"WebSocket error for user {user_id}: {e}")
        finally:
            await pubsub.unsubscribe(channel_name)

    async def send_personal_message(self, message: dict, user_id: str):
        from fastapi.encoders import jsonable_encoder
        encoded_message = jsonable_encoder(message)
        if db_client.redis:
            await db_client.redis.publish(f"chat_delivery:{user_id}", json.dumps(encoded_message))
        else:
            if user_id in self.active_connections:
                await self.active_connections[user_id].send_text(json.dumps(encoded_message))

manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id)

@router.post("/tin-nhan", response_model=APIResponse[Any])
async def send_message(req: MessageCreate, current_user: UserInDB = Depends(get_current_user)):
    msg = await ChatService.send_message(
        req.receiver_id, 
        req.content, 
        current_user, 
        req.image_url, 
        req.reply_to_id,
        req.audio_url
    )
    await manager.send_personal_message({
        "type": "new_message",
        "data": msg
    }, req.receiver_id)
    
    return APIResponse(
        data=msg, 
        message="Gửi tin nhắn thành công", 
        status=201
    )

@router.get("/tin-nhan/{other_user_id}", response_model=APIResponse[Any])
async def get_messages(other_user_id: str, cursor: str = None, limit: int = Query(50), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ChatService.get_messages(other_user_id, current_user, limit, cursor), message="Lấy lịch sử tin nhắn thành công", status=200)

@router.get("/hoi-thoai", response_model=APIResponse[Any])
async def get_conversations(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ChatService.get_conversations(current_user), message="Lấy danh sách hội thoại thành công", status=200)

@router.post("/ghim/{message_id}", response_model=APIResponse[Any])
async def toggle_pin(message_id: str, current_user: UserInDB = Depends(get_current_user)):
    result = await ChatService.toggle_pin(message_id, current_user)
    if result is None:
        return APIResponse(message="Không tìm thấy tin nhắn hoặc không có quyền", status=404)
    if result == "limit_reached":
        return APIResponse(message="Bạn chỉ có thể ghim tối đa 3 tin nhắn", status=400)
    
    other_id = result["receiver_id"] if result["sender_id"] == current_user.id else result["sender_id"]
    await manager.send_personal_message({
        "type": "message_pinned",
        "data": result
    }, other_id)
    
    return APIResponse(data=result["is_pinned"], message="Cập nhật trạng thái ghim thành công", status=200)

@router.put("/chinh-sua/{message_id}", response_model=APIResponse[Any])
async def edit_message(message_id: str, req: dict, current_user: UserInDB = Depends(get_current_user)):
    content = req.get("content")
    if not content:
        return APIResponse(message="Nội dung không được để trống", status=400)
    result = await ChatService.edit_message(message_id, content, current_user)
    if not result:
        return APIResponse(message="Không thể chỉnh sửa tin nhắn này", status=403)
    
    other_id = result["receiver_id"] if result["sender_id"] == current_user.id else result["sender_id"]
    await manager.send_personal_message({
        "type": "message_edited",
        "data": result
    }, other_id)
    
    return APIResponse(data=result, message="Chỉnh sửa tin nhắn thành công", status=200)

@router.delete("/tin-nhan/{message_id}", response_model=APIResponse[Any])
async def recall_message(message_id: str, current_user: UserInDB = Depends(get_current_user)):
    result = await ChatService.recall_message(message_id, current_user)
    if not result:
        return APIResponse(message="Không có quyền thu hồi tin nhắn này", status=403)
        
    other_id = result["receiver_id"] if result["sender_id"] == current_user.id else result["sender_id"]
    await manager.send_personal_message({
        "type": "message_recalled",
        "data": result
    }, other_id)
    
    return APIResponse(data=result, message="Đã thu hồi tin nhắn thành công", status=200)

@router.get("/tim-kiem/{other_user_id}", response_model=APIResponse[Any])
async def search_messages(other_user_id: str, q: str = Query(...), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ChatService.search_messages(other_user_id, q, current_user),
        message="Tìm kiếm tin nhắn thành công"
    )

@router.post("/tin-nhan/{message_id}/cam-xuc", response_model=APIResponse[Any])
async def add_reaction(message_id: str, req: dict, current_user: UserInDB = Depends(get_current_user)):
    reaction = req.get("reaction")
    result = await ChatService.add_reaction(message_id, reaction, current_user)
    if not result:
        return APIResponse(message="Không thể bày tỏ cảm xúc", status=400)
        
    other_id = result["receiver_id"] if result["sender_id"] == current_user.id else result["sender_id"]
    await manager.send_personal_message({
        "type": "message_reaction",
        "data": result
    }, other_id)
    
    return APIResponse(data=result, message="Đã cập nhật biểu cảm thành công")

@router.post("/doc-tin-nhan/{other_user_id}", response_model=APIResponse[Any])
async def mark_as_read(other_user_id: str, current_user: UserInDB = Depends(get_current_user)):
    result = await ChatService.mark_as_read(other_user_id, current_user)
    
    await manager.send_personal_message({
        "type": "messages_read",
        "data": {"reader_id": current_user.id}
    }, other_user_id)
    
    return APIResponse(data=result, message="Đã đánh dấu đã xem thành công")

@router.post("/chia-se-tai-lieu/{receiver_id}", response_model=APIResponse[Any])
async def share_document(receiver_id: str, req: dict, current_user: UserInDB = Depends(get_current_user)):
    document_id = req.get("document_id")
    if not document_id:
        return APIResponse(message="Thiếu mã tài liệu chia sẻ", status=400)
    result = await ChatService.share_document(receiver_id, document_id, current_user)
    if not result:
        return APIResponse(message="Không tìm thấy tài liệu chia sẻ", status=404)
        
    await manager.send_personal_message({
        "type": "new_message",
        "data": result
    }, receiver_id)
    
    return APIResponse(data=result, message="Chia sẻ tài liệu thành công", status=201)

@router.get("/tai-lieu-chia-se/{other_user_id}", response_model=APIResponse[Any])
async def get_shared_attachments(other_user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ChatService.get_shared_attachments(other_user_id, current_user), message="Lấy tệp chia sẻ thành công")

@router.post("/chan/{other_user_id}", response_model=APIResponse[Any])
async def block_user(other_user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ChatService.block_user(other_user_id, current_user), message="Đã chặn người dùng")

@router.post("/bo-chan/{other_user_id}", response_model=APIResponse[Any])
async def unblock_user(other_user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ChatService.unblock_user(other_user_id, current_user), message="Đã bỏ chặn người dùng")

@router.get("/trang-thai-chan/{other_user_id}", response_model=APIResponse[Any])
async def get_blocked_status(other_user_id: str, current_user: UserInDB = Depends(get_current_user)):
    blocked = await ChatService.check_blocked_status(str(current_user.id), other_user_id)
    return APIResponse(data={"is_blocked": blocked}, message="Lấy trạng thái chặn thành công")

@router.post("/ghim-hoi-thoai/{other_user_id}", response_model=APIResponse[Any])
async def toggle_pin_conversation(other_user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ChatService.toggle_pin_conversation(other_user_id, current_user), message="Cập nhật ghim hội thoại thành công")

@router.post("/dich/{message_id}", response_model=APIResponse[Any])
async def translate_message(message_id: str, req: dict, current_user: UserInDB = Depends(get_current_user)):
    target_lang = req.get("target_lang", "vi")
    result = await ChatService.translate_message(message_id, target_lang, current_user)
    if not result:
        return APIResponse(message="Không tìm thấy tin nhắn", status=404)
        
    other_id = result.get("receiver_id")
    if other_id:
        await manager.send_personal_message({
            "type": "message_translated",
            "data": {**result, "message_id": message_id}
        }, other_id)
        
    return APIResponse(data=result, message="Dịch tin nhắn thành công")

@router.post("/nhom", response_model=APIResponse[Any])
async def create_group(req: dict, current_user: UserInDB = Depends(get_current_user)):
    group_name = req.get("group_name")
    member_ids = req.get("member_ids", [])
    if not group_name:
        return APIResponse(message="Tên nhóm không được để trống", status=400)
    result = await ChatService.create_group(group_name, member_ids, current_user)
    return APIResponse(data=result, message="Tạo nhóm thảo luận thành công", status=201)

@router.post("/nhap-tin-nhan/{other_user_id}", response_model=APIResponse[Any])
async def save_draft(other_user_id: str, req: dict, current_user: UserInDB = Depends(get_current_user)):
    content = req.get("content", "")
    result = await ChatService.save_draft(other_user_id, content, current_user)
    return APIResponse(data=result, message="Đã lưu tin nhắn nháp")

@router.get("/nhap-tin-nhan/{other_user_id}", response_model=APIResponse[Any])
async def get_draft(other_user_id: str, current_user: UserInDB = Depends(get_current_user)):
    result = await ChatService.get_draft(other_user_id, current_user)
    return APIResponse(data=result, message="Lấy tin nhắn nháp thành công")

@router.post("/tu-huy/{other_user_id}", response_model=APIResponse[Any])
async def toggle_self_destruct(other_user_id: str, req: dict, current_user: UserInDB = Depends(get_current_user)):
    seconds = req.get("seconds", 0)
    result = await ChatService.toggle_self_destruct(other_user_id, seconds, current_user)
    
    await manager.send_personal_message({
        "type": "conversation_settings_updated",
        "data": {"self_destruct_seconds": seconds}
    }, other_user_id)
    
    return APIResponse(data=result, message="Cập nhật bộ tự hủy thành công")

@router.post("/tat-am/{other_user_id}", response_model=APIResponse[Any])
async def toggle_mute(other_user_id: str, current_user: UserInDB = Depends(get_current_user)):
    result = await ChatService.toggle_mute(other_user_id, current_user)
    return APIResponse(data=result, message="Đã cập nhật trạng thái tắt âm")

@router.get("/cai-dat/{other_user_id}", response_model=APIResponse[Any])
async def get_conversation_settings(other_user_id: str, current_user: UserInDB = Depends(get_current_user)):
    result = await ChatService.get_conversation_settings(other_user_id, current_user)
    
    is_online = other_user_id in manager.active_connections
    result["is_online"] = is_online
    return APIResponse(data=result, message="Lấy cài đặt thành công")
    
@router.delete("/hoi-thoai/{other_user_id}", response_model=APIResponse[Any])
async def delete_conversation(other_user_id: str, current_user: UserInDB = Depends(get_current_user)):
    result = await ChatService.delete_conversation(other_user_id, current_user)
    return APIResponse(data=result, message="Xóa cuộc hội thoại thành công")


