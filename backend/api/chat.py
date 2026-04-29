from typing import Any, List
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query
from api.dependencies import get_current_user
from models.user import UserInDB
from models.chat import MessageCreate, MessageResponse, ConversationResponse
from services.chat import ChatService

router = APIRouter(prefix="/chat")

@router.post("/messages", response_model=APIResponse[Any])
async def send_message(req: MessageCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ChatService.send_message(req.receiver_id, req.content, current_user), message="Gửi tin nhắn thành công.", status=201)

@router.get("/messages/{other_user_id}", response_model=APIResponse[Any])
async def get_messages(other_user_id: str, limit: int = Query(50), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ChatService.get_messages(other_user_id, current_user, limit), message="Lấy lịch sử tin nhắn thành công.", status=200)

@router.get("/conversations", response_model=APIResponse[Any])
async def get_conversations(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ChatService.get_conversations(current_user), message="Lấy danh sách hội thoại thành công.", status=200)
