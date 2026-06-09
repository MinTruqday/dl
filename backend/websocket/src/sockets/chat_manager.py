from fastapi import WebSocket
from typing import Dict, List
from loguru import logger
import asyncio
import json

class ChatManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.redis_client = None
        self.pubsub = None

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected to chat. Total devices: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections and websocket in self.active_connections[user_id]:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected from chat.")

    async def broadcast_to_user(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            data = json.dumps(message)
            dead_connections = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(data)
                except Exception as e:
                    logger.warning(f"Error sending message to {user_id}: {e}")
                    dead_connections.append(connection)
            for dead in dead_connections:
                self.disconnect(dead, user_id)

    async def listen_redis(self):
        if not self.redis_client:
            return
        self.pubsub = self.redis_client.pubsub()
        await self.pubsub.subscribe("chat_channel")
        logger.info("ChatManager subscribed to Redis chat_channel")
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    receiver_id = data.get("receiver_id")
                    if receiver_id:
                        await self.broadcast_to_user(receiver_id, data)
        except Exception as e:
            logger.error(f"Redis chat_channel listener error: {e}")

chat_manager = ChatManager()
