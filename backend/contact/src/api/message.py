from typing import Any, List
from src.core.response import APIResponse
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from src.api.dependency import get_db, get_current_user
from src.schemas.user import UserInDB
from src.schemas.message import MessageCreate, MessageResponse, ConversationResponse
from src.services.message import MessageService
from src.core.database import db_client
from loguru import logger
import json
import asyncio
router = APIRouter(prefix='/tro-chuyen')

@router.post('/tin-nhan', response_model=APIResponse[Any])
async def send_message(req: MessageCreate, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    msg = await MessageService.send_message(req.receiver_id, req.content, current_user, req.image_url, req.reply_to_id, req.audio_url, req.client_msg_id, db=db)
    if db_client.redis:
        await db_client.redis.publish("chat_channel", json.dumps({"receiver_id": 'data': msg}, req.receiver_id, **{'type': 'new_message'}))
    return APIResponse(data=msg, message='Gửi tin nhắn thành công', status=201)

@router.get('/tin-nhan/{other_user_id}', response_model=APIResponse[Any])
async def get_messages(other_user_id: str, cursor: str=None, limit: int=Query(50), current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await MessageService.get_messages(other_user_id, current_user, limit, cursor, db=db), message='Lấy lịch sử tin nhắn thành công', status=200)

@router.get('/hoi-thoai', response_model=APIResponse[Any])
async def get_conversations(current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await MessageService.get_conversations(current_user, db=db), message='Lấy danh sách hội thoại thành công', status=200)

@router.post('/ghim/{message_id}', response_model=APIResponse[Any])
async def toggle_pin(message_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    result = await MessageService.toggle_pin(message_id, current_user, db=db)
    if result is None:
        return APIResponse(message='Không tìm thấy tin nhắn hoặc không có quyền', status=404)
    if result == 'limit_reached':
        return APIResponse(message='Bạn chỉ có thể ghim tối đa 3 tin nhắn', status=400)
    other_id = result['receiver_id'] if result['sender_id'] == current_user.id else result['sender_id']
    if db_client.redis:
        await db_client.redis.publish("chat_channel", json.dumps({"receiver_id": 'data': result}, other_id, **{'type': 'message_pinned'}))
    return APIResponse(data=result['is_pinned'], message='Cập nhật trạng thái ghim thành công', status=200)

@router.put('/chinh-sua/{message_id}', response_model=APIResponse[Any])
async def edit_message(message_id: str, req: dict, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    content = req.get('content')
    if not content:
        return APIResponse(message='Nội dung không được để trống', status=400)
    result = await MessageService.edit_message(message_id, content, current_user, db=db)
    if not result:
        return APIResponse(message='Không thể chỉnh sửa tin nhắn này', status=403)
    other_id = result['receiver_id'] if result['sender_id'] == current_user.id else result['sender_id']
    if db_client.redis:
        await db_client.redis.publish("chat_channel", json.dumps({"receiver_id": 'data': result}, other_id, **{'type': 'message_edited'}))
    return APIResponse(data=result, message='Chỉnh sửa tin nhắn thành công', status=200)

@router.delete('/tin-nhan/{message_id}', response_model=APIResponse[Any])
async def recall_message(message_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    result = await MessageService.recall_message(message_id, current_user, db=db)
    if not result:
        return APIResponse(message='Không có quyền thu hồi tin nhắn này', status=403)
    other_id = result['receiver_id'] if result['sender_id'] == current_user.id else result['sender_id']
    if db_client.redis:
        await db_client.redis.publish("chat_channel", json.dumps({"receiver_id": 'data': result}, other_id, **{'type': 'message_recalled'}))
    return APIResponse(data=result, message='Đã thu hồi tin nhắn thành công', status=200)

@router.get('/tim-kiem/{other_user_id}', response_model=APIResponse[Any])
async def search_messages(other_user_id: str, q: str=Query(...), current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await MessageService.search_messages(other_user_id, q, current_user, db=db), message='Tìm kiếm tin nhắn thành công')

@router.post('/tin-nhan/{message_id}/cam-xuc', response_model=APIResponse[Any])
async def add_reaction(message_id: str, req: dict, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    reaction = req.get('reaction')
    result = await MessageService.add_reaction(message_id, reaction, current_user, db=db)
    if not result:
        return APIResponse(message='Không thể bày tỏ cảm xúc', status=400)
    other_id = result['receiver_id'] if result['sender_id'] == current_user.id else result['sender_id']
    if db_client.redis:
        await db_client.redis.publish("chat_channel", json.dumps({"receiver_id": 'data': result}, other_id, **{'type': 'message_reaction'}))
    return APIResponse(data=result, message='Đã cập nhật biểu cảm thành công')

@router.post('/doc-tin-nhan/{other_user_id}', response_model=APIResponse[Any])
async def mark_as_read(other_user_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    result = await MessageService.mark_as_read(other_user_id, current_user, db=db)
    if db_client.redis:
        await db_client.redis.publish("chat_channel", json.dumps({"receiver_id": 'data': {'reader_id': current_user.id}}, other_user_id, **{'type': 'messages_read'}))
    return APIResponse(data=result, message='Đã đánh dấu đã xem thành công')

@router.post('/chia-se-tai-lieu/{receiver_id}', response_model=APIResponse[Any])
async def share_document(receiver_id: str, req: dict, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    document_id = req.get('document_id')
    if not document_id:
        return APIResponse(message='Thiếu mã tài liệu chia sẻ', status=400)
    result = await MessageService.share_document(receiver_id, document_id, current_user, db=db)
    if not result:
        return APIResponse(message='Không tìm thấy tài liệu chia sẻ', status=404)
    if db_client.redis:
        await db_client.redis.publish("chat_channel", json.dumps({"receiver_id": 'data': result}, receiver_id, **{'type': 'new_message'}))
    return APIResponse(data=result, message='Chia sẻ tài liệu thành công', status=201)

@router.get('/tai-lieu-chia-se/{other_user_id}', response_model=APIResponse[Any])
async def get_shared_attachments(other_user_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await MessageService.get_shared_attachments(other_user_id, current_user, db=db), message='Lấy tệp chia sẻ thành công')

@router.post('/chan/{other_user_id}', response_model=APIResponse[Any])
async def block_user(other_user_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await MessageService.block_user(other_user_id, current_user, db=db), message='Đã chặn người dùng')

@router.post('/bo-chan/{other_user_id}', response_model=APIResponse[Any])
async def unblock_user(other_user_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await MessageService.unblock_user(other_user_id, current_user, db=db), message='Đã bỏ chặn người dùng')

@router.get('/trang-thai-chan/{other_user_id}', response_model=APIResponse[Any])
async def get_blocked_status(other_user_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    blocked = await MessageService.check_blocked_status(str(current_user.id), other_user_id, db=db)
    return APIResponse(data={'is_blocked': blocked}, message='Lấy trạng thái chặn thành công')

@router.post('/ghim-hoi-thoai/{other_user_id}', response_model=APIResponse[Any])
async def toggle_pin_conversation(other_user_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await MessageService.toggle_pin_conversation(other_user_id, current_user, db=db), message='Cập nhật ghim hội thoại thành công')

@router.post('/dich/{message_id}', response_model=APIResponse[Any])
async def translate_message(message_id: str, req: dict, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    target_lang = req.get('target_lang', 'vi')
    result = await MessageService.translate_message(message_id, target_lang, current_user, db=db)
    if not result:
        return APIResponse(message='Không tìm thấy tin nhắn', status=404)
    other_id = result.get('receiver_id')
    if other_id:
        if db_client.redis:
        await db_client.redis.publish("chat_channel", json.dumps({"receiver_id": 'data': {**result, 'message_id': message_id}}, other_id, **{'type': 'message_translated'}))
    return APIResponse(data=result, message='Dịch tin nhắn thành công')

@router.post('/nhom', response_model=APIResponse[Any])
async def create_group(req: dict, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    group_name = req.get('group_name')
    member_ids = req.get('member_ids', [])
    if not group_name:
        return APIResponse(message='Tên nhóm không được để trống', status=400)
    result = await MessageService.create_group(group_name, member_ids, current_user, db=db)
    return APIResponse(data=result, message='Tạo nhóm thảo luận thành công', status=201)

@router.post('/nhap-tin-nhan/{other_user_id}', response_model=APIResponse[Any])
async def save_draft(other_user_id: str, req: dict, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    content = req.get('content', '')
    result = await MessageService.save_draft(other_user_id, content, current_user, db=db)
    return APIResponse(data=result, message='Đã lưu tin nhắn nháp')

@router.get('/nhap-tin-nhan/{other_user_id}', response_model=APIResponse[Any])
async def get_draft(other_user_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    result = await MessageService.get_draft(other_user_id, current_user, db=db)
    return APIResponse(data=result, message='Lấy tin nhắn nháp thành công')

@router.post('/tu-huy/{other_user_id}', response_model=APIResponse[Any])
async def toggle_self_destruct(other_user_id: str, req: dict, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    seconds = req.get('seconds', 0)
    result = await MessageService.toggle_self_destruct(other_user_id, seconds, current_user, db=db)
    if db_client.redis:
        await db_client.redis.publish("chat_channel", json.dumps({"receiver_id": 'data': {'self_destruct_seconds': seconds}}, other_user_id, **{'type': 'conversation_settings_updated'}))
    return APIResponse(data=result, message='Cập nhật bộ tự hủy thành công')

@router.post('/tat-am/{other_user_id}', response_model=APIResponse[Any])
async def toggle_mute(other_user_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    result = await MessageService.toggle_mute(other_user_id, current_user, db=db)
    return APIResponse(data=result, message='Đã cập nhật trạng thái tắt âm')

@router.get('/cai-dat/{other_user_id}', response_model=APIResponse[Any])
async def get_conversation_settings(other_user_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    result = await MessageService.get_conversation_settings(other_user_id, current_user, db=db)
    is_online = other_user_id in manager.active_connections
    result['is_online'] = is_online
    return APIResponse(data=result, message='Lấy cài đặt thành công')

@router.delete('/hoi-thoai/{other_user_id}', response_model=APIResponse[Any])
async def delete_conversation(other_user_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    result = await MessageService.delete_conversation(other_user_id, current_user, db=db)
    return APIResponse(data=result, message='Xóa cuộc hội thoại thành công')