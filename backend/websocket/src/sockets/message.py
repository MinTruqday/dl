from src.core.infrastructure.redis import redis
import asyncio
import json
from typing import Any, List

import httpx
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.mq import mq

class MessageSocket:
    def __init__(self):
        self.active_connections: dict[str, set[WebSocket]] = {}
        self._pubsub = None
        self._listener_task = None

    async def _ensure_listener(self):
        if self._listener_task is not None:
            return
        if not redis.get_client():
            return
        self._pubsub = redis.get_client().pubsub()
        await self._pubsub.psubscribe("chat_delivery:*")
        self._listener_task = asyncio.create_task(self._global_listener())

    async def _global_listener(self):
        try:
            while True:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message and message["type"] == "pmessage":
                    channel = message["channel"]
                    if isinstance(channel, bytes):
                        channel = channel.decode("utf-8")
                    user_id = channel.split(":", 1)[1]
                    ws_set = self.active_connections.get(user_id)
                    if ws_set:
                        disconnected = []
                        data_str = message["data"]
                        if isinstance(data_str, bytes):
                            data_str = data_str.decode("utf-8")
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
            logger.exception("Background message pubsub listener connection failed")
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
        pass

    async def _handle_ws_action(self, user_id: str, payload: dict):
        action = payload.get("action")
        data = payload.get("data", {})
        await mq.publish(
            "messaging_queue",
            {
                "ws_action": action,
                "user_id": user_id,
                "data": data
            }
        )

message_manager = MessageSocket()
