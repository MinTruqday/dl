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

class ConnectionManager:

    def __init__(self):
        self.active_connections: dict[str, set[WebSocket]] = {}
        self._pubsub = None
        self._listener_task = None

    async def _ensure_listener(self):
        if self._listener_task is not None:
            return
        if not db_client.redis:
            return
        self._pubsub = db_client.redis.pubsub()
        await self._pubsub.psubscribe('chat_delivery:*')
        self._listener_task = asyncio.create_task(self._global_listener())

    async def _global_listener(self):
        try:
            while True:
                message = await self._pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message['type'] == 'pmessage':
                    channel = message['channel']
                    if isinstance(channel, bytes):
                        channel = channel.decode('utf-8')
                    user_id = channel.split(':', 1)[1]
                    ws_set = self.active_connections.get(user_id)
                    if ws_set:
                        disconnected = []
                        data_str = message['data']
                        if isinstance(data_str, bytes):
                            data_str = data_str.decode('utf-8')
                        for ws in list(ws_set):
                            try:
                                await ws.send_text(data_str)
                            except Exception:
                                disconnected.append(ws)
                        for ws in disconnected:
                            self.disconnect(user_id, ws)
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f'Global Redis listener crashed: {e}')
            self._listener_task = None

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        await self._ensure_listener()

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, receiver_id: str):
        from fastapi.encoders import jsonable_encoder
        encoded_message = jsonable_encoder(message)
        payload = json.dumps(encoded_message)
        targets = [receiver_id]
        if receiver_id.startswith('group_'):
            db = db_client.mongodb.get_default_database()
            group = await db['chat_groups'].find_one({'_id': receiver_id})
            if group:
                targets = group.get('members', [])
        for target_id in targets:
            if db_client.redis:
                await db_client.redis.publish(f'chat_delivery:{target_id}', payload)
            else:
                ws_set = self.active_connections.get(target_id)
                if ws_set:
                    disconnected = []
                    for ws in list(ws_set):
                        try:
                            await ws.send_text(payload)
                        except Exception:
                            disconnected.append(ws)
                    for ws in disconnected:
                        self.disconnect(target_id, ws)

    async def _handle_ws_action(self, user_id: str, payload: dict):
        action = payload.get('action')
        data = payload.get('data', {})
        if action == 'send_message':
            await self._action_send_message(user_id, data)
        elif action == 'mark_read':
            await self._action_mark_read(user_id, data)
        elif action == 'typing':
            await self._action_typing(user_id, data)
        elif action == 'sync':
            await self._action_sync(user_id, data)

    async def _action_sync(self, user_id: str, data: dict):
        last_message_id = data.get('last_message_id')
        db = db_client.mongodb.get_default_database()
        ws_set = self.active_connections.get(user_id)
        if not ws_set:
            return
        disconnected = []
        if last_message_id:
            groups = await db['chat_groups'].find({'members': user_id}).to_list(100)
            group_ids = [g['_id'] for g in groups]
            query = {'_id': {'$gt': last_message_id}, '$or': [{'receiver_id': user_id}, {'sender_id': user_id}, {'receiver_id': {'$in': group_ids}}]}
            new_messages = await db['messages'].find(query).sort('created_at', 1).to_list(length=200)
            for msg in new_messages:
                msg['_id'] = str(msg['_id'])
                payload = json.dumps({'type': 'new_message', 'data': msg})
                for ws in list(ws_set):
                    try:
                        await ws.send_text(payload)
                    except Exception:
                        disconnected.append(ws)
        active_finetunes = await db['finetune_jobs'].find({'status': {'$in': ['running', 'pending']}}).to_list(50)
        active_collectors = await db['collection_jobs'].find({'status': {'$in': ['running', 'pending']}}).to_list(50)
        job_payload = json.dumps({'type': 'global_sync_jobs', 'data': {'finetune': [{'id': str(j['_id']), 'progress': j.get('progress', 0), 'status': j['status']} for j in active_finetunes], 'collector': [{'id': str(j['_id']), 'progress': j.get('progress', 0), 'status': j['status']} for j in active_collectors]}})
        for ws in list(ws_set):
            try:
                await ws.send_text(job_payload)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(user_id, ws)

    async def _action_send_message(self, sender_id: str, data: dict):
        receiver_id = data.get('receiver_id')
        content = data.get('content', '')
        image_url = data.get('image_url')
        reply_to_id = data.get('reply_to_id')
        audio_url = data.get('audio_url')
        client_msg_id = data.get('client_msg_id')
        if not receiver_id:
            return
        db = db_client.mongodb.get_default_database()
        sender_doc = await db['users'].find_one({'_id': sender_id}, {'full_name': 1, 'username': 1})
        if not sender_doc:
            return

        class _FakeUser:

            def __init__(self, uid, doc):
                self.id = uid
                self.full_name = doc.get('full_name', '')
                self.username = doc.get('username', '')
        fake_user = _FakeUser(sender_id, sender_doc)
        msg = await MessageService.send_message(receiver_id, content, fake_user, image_url, reply_to_id, audio_url, client_msg_id)
        await self.send_personal_message({'type': 'new_message', 'data': msg}, receiver_id)
        await self.send_personal_message({'type': 'message_sent_ack', 'data': msg}, sender_id)

    async def _action_mark_read(self, user_id: str, data: dict):
        other_user_id = data.get('other_user_id')
        if not other_user_id:
            return
        db = db_client.mongodb.get_default_database()

        class _FakeUser:

            def __init__(self, uid):
                self.id = uid
        await MessageService.mark_as_read(other_user_id, _FakeUser(user_id))
        await self.send_personal_message({'type': 'messages_read', 'data': {'reader_id': user_id}}, other_user_id)

    async def _action_typing(self, user_id: str, data: dict):
        other_user_id = data.get('other_user_id')
        if not other_user_id:
            return
        await self.send_personal_message({'type': 'typing_indicator', 'data': {'user_id': user_id}}, other_user_id)
manager = ConnectionManager()

@router.websocket('/ws/{user_id}')
async def websocket_endpoint(websocket: WebSocket, user_id: str, token: str=Query(...), db=Depends(get_db)):
    try:
        user = await get_current_user_from_token(token)
        if str(user.id) != user_id:
            await websocket.close(code=1008)
            return
    except Exception:
        await websocket.close(code=1008)
        return
    import time
    db = db_client.redis
    if db:
        is_banned = await db.get(f'ws_ban:{user_id}')
        if is_banned:
            await websocket.close(code=1008)
            return
    await manager.connect(user_id, websocket)
    frame_times = []
    try:
        while True:
            raw = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
            now = time.time()
            frame_times.append(now)
            frame_times = [t for t in frame_times if now - t <= 1.0]
            if len(frame_times) > 5:
                if db:
                    await db.setex(f'ws_ban:{user_id}', 300, 'banned')
                manager.disconnect(user_id, websocket)
                await websocket.close(code=1008)
                return
            try:
                payload = json.loads(raw)
                if payload.get('action') == 'ping':
                    await websocket.send_json({'type': 'pong'})
                    continue
                await manager._handle_ws_action(user_id, payload)
            except json.JSONDecodeError:
                pass
    except asyncio.TimeoutError:
        manager.disconnect(user_id, websocket)
        try:
            await websocket.close(code=1000)
        except Exception:
            pass
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)

@router.post('/tin-nhan', response_model=APIResponse[Any])
async def send_message(req: MessageCreate, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    msg = await MessageService.send_message(req.receiver_id, req.content, current_user, req.image_url, req.reply_to_id, req.audio_url, req.client_msg_id, db=db)
    await manager.send_personal_message({'type': 'new_message', 'data': msg}, req.receiver_id)
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
    await manager.send_personal_message({'type': 'message_pinned', 'data': result}, other_id)
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
    await manager.send_personal_message({'type': 'message_edited', 'data': result}, other_id)
    return APIResponse(data=result, message='Chỉnh sửa tin nhắn thành công', status=200)

@router.delete('/tin-nhan/{message_id}', response_model=APIResponse[Any])
async def recall_message(message_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    result = await MessageService.recall_message(message_id, current_user, db=db)
    if not result:
        return APIResponse(message='Không có quyền thu hồi tin nhắn này', status=403)
    other_id = result['receiver_id'] if result['sender_id'] == current_user.id else result['sender_id']
    await manager.send_personal_message({'type': 'message_recalled', 'data': result}, other_id)
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
    await manager.send_personal_message({'type': 'message_reaction', 'data': result}, other_id)
    return APIResponse(data=result, message='Đã cập nhật biểu cảm thành công')

@router.post('/doc-tin-nhan/{other_user_id}', response_model=APIResponse[Any])
async def mark_as_read(other_user_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    result = await MessageService.mark_as_read(other_user_id, current_user, db=db)
    await manager.send_personal_message({'type': 'messages_read', 'data': {'reader_id': current_user.id}}, other_user_id)
    return APIResponse(data=result, message='Đã đánh dấu đã xem thành công')

@router.post('/chia-se-tai-lieu/{receiver_id}', response_model=APIResponse[Any])
async def share_document(receiver_id: str, req: dict, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    document_id = req.get('document_id')
    if not document_id:
        return APIResponse(message='Thiếu mã tài liệu chia sẻ', status=400)
    result = await MessageService.share_document(receiver_id, document_id, current_user, db=db)
    if not result:
        return APIResponse(message='Không tìm thấy tài liệu chia sẻ', status=404)
    await manager.send_personal_message({'type': 'new_message', 'data': result}, receiver_id)
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
        await manager.send_personal_message({'type': 'message_translated', 'data': {**result, 'message_id': message_id}}, other_id)
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
    await manager.send_personal_message({'type': 'conversation_settings_updated', 'data': {'self_destruct_seconds': seconds}}, other_user_id)
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