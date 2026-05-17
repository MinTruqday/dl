import asyncio
import json
from loguru import logger
from fastapi import WebSocket
from core.database import db_client

class ChatConnectionManager:
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
            logger.error(f"Redis chat listener error for {user_id}: {e}")
        finally:
            await pubsub.unsubscribe(channel_name)

manager = ChatConnectionManager()
