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



async def send_personal_message(message: dict, user_id: str):
    if db_client.redis:
        await db_client.redis.publish(f"chat_delivery:{user_id}", json.dumps(message))

@router.post("/tin-nhan", response_model=APIResponse[Any])
async def send_message(req: MessageCreate, current_user: UserInDB = Depends(get_current_user)):
    msg = await ChatService.send_message(
        req.receiver_id, 
        req.content, 
        current_user, 
        req.image_url, 
        req.reply_to_id
    )
    await send_personal_message({
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
    await send_personal_message({
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
    await send_personal_message({
        "type": "message_edited",
        "data": result
    }, other_id)
    
    return APIResponse(data=result, message="Chỉnh sửa tin nhắn thành công", status=200)
