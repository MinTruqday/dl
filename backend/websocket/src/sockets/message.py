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
        await self._pubsub.psubscribe("message_delivery:*")
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
        
        r = redis.get_client()
        if r:
            await r.setex(f"user_online:{user_id}", 90, "true")

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                r = redis.get_client()
                if r:
                    import time
                    async def update_offline():
                        await r.delete(f"user_online:{user_id}")
                        await r.set(f"user_last_active:{user_id}", str(int(time.time())))
                    asyncio.create_task(update_offline())

    async def send_personal_message(self, message: dict, receiver_id: str):
        pass

    async def _handle_ws_action(self, user_id: str, payload: dict):
        action = payload.get("action")
        data = payload.get("data", {})
        r = redis.get_client()
        
        if action in ("typing_start", "typing_end"):
            receiver_id = data.get("receiver_id")
            if receiver_id and r:
                event = {
                    "type": action,
                    "data": {
                        "sender_id": user_id,
                        "receiver_id": receiver_id
                    }
                }
                await r.publish(f"message_delivery:{receiver_id}", json.dumps(event))
            return
            
        if action == "check_online":
            user_ids = data.get("user_ids", [])
            if not user_ids or not isinstance(user_ids, list):
                return
            status_map = {}
            if r:
                for uid in user_ids:
                    is_online = await r.exists(f"user_online:{uid}")
                    if is_online:
                        status_map[uid] = True
                    else:
                        last_active = await r.get(f"user_last_active:{uid}")
                        if last_active:
                            try:
                                status_map[uid] = int(last_active.decode("utf-8"))
                            except ValueError:
                                status_map[uid] = False
                        else:
                            status_map[uid] = False
            ws_set = self.active_connections.get(user_id)
            if ws_set:
                for ws in list(ws_set):
                    try:
                        await ws.send_json({"type": "online_status", "data": status_map})
                    except Exception:
                        pass
            return

        await mq.publish(
            "messaging_queue",
            {
                "ws_action": action,
                "user_id": user_id,
                "data": data
            }
        )

message_manager = MessageSocket()
