from typing import Any, List
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
import json
import asyncio
from src.core.database import db_client
import httpx
from core.config import settings

class MessageConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, set[WebSocket]] = {}
        self._pubsub = None
        self._listener_task = None

    async def _ensure_listener(self):
        if self._listener_task is not None:
            return
        if not db_client.redis:
            return
        # Create a new non-decoded redis client for pubsub if needed, or use the existing
        # db_client.redis is already initialized.
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
        payload = json.dumps(message)
        targets = [receiver_id]
        if receiver_id.startswith('group_'):
            if db_client.mongodb:
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
        if action == 'mark_read':
            await self._action_mark_read(user_id, data)
        elif action == 'typing':
            await self._action_typing(user_id, data)
        elif action == 'sync':
            await self._action_sync(user_id, data)

    async def _action_sync(self, user_id: str, data: dict):
        last_message_id = data.get('last_message_id')
        if not db_client.mongodb:
            return
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
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{settings.COLLECTOR_URL}/noi-bo/cong-viec-dang-chay", timeout=3.0)
                active_collectors = res.json() if res.status_code == 200 else []
        except Exception:
            active_collectors = []
        job_payload = json.dumps({'type': 'global_sync_jobs', 'data': {'finetune': [{'id': str(j['_id']), 'progress': j.get('progress', 0), 'status': j['status']} for j in active_finetunes], 'collector': active_collectors}})
        for ws in list(ws_set):
            try:
                await ws.send_text(job_payload)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(user_id, ws)



    async def _action_mark_read(self, user_id: str, data: dict):
        other_user_id = data.get('other_user_id')
        if not other_user_id:
            return
        if not db_client.mongodb:
            return
        db = db_client.mongodb.get_default_database()
        await db['messages'].update_many(
            {'sender_id': other_user_id, 'receiver_id': user_id, 'is_read': False},
            {'$set': {'is_read': True}}
        )
        await self.send_personal_message({'type': 'messages_read', 'data': {'reader_id': user_id}}, other_user_id)

    async def _action_typing(self, user_id: str, data: dict):
        other_user_id = data.get('other_user_id')
        if not other_user_id:
            return
        await self.send_personal_message({'type': 'typing_indicator', 'data': {'user_id': user_id}}, other_user_id)

message_manager = MessageConnectionManager()
