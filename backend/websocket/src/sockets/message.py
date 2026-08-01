import asyncio
import json
import time
import uuid
from contextlib import suppress

from fastapi import WebSocket
from loguru import logger

from src.core.infrastructure.configuration import settings
from src.core.internal_services import allowed_contacts
from src.core.infrastructure.database import database


class MessageSocket:
    def __init__(self):
        self.instance_id = str(uuid.uuid4())
        self.active_connections: dict[str, dict[WebSocket, str]] = {}
        self._pubsub = None
        self._listener_task = None
        self._presence_task = None

    async def start(self):
        if self._listener_task and not self._listener_task.done():
            return
        self._pubsub = database.redis.pubsub()
        await self._pubsub.psubscribe("message_delivery:*")
        self._listener_task = asyncio.create_task(self._global_listener())
        self._presence_task = asyncio.create_task(self._presence_loop())

    async def _global_listener(self):
        while True:
            try:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1,
                )
                if not message:
                    await asyncio.sleep(0.02)
                    continue
                try:
                    data = str(message["data"])
                    if len(data.encode("utf-8")) > settings.MAX_WS_MESSAGE_BYTES:
                        continue
                    channel = str(message["channel"])
                    user_id = channel.split(":", 1)[1]
                    dead = []
                    for socket in list(self.active_connections.get(user_id, {})):
                        try:
                            await socket.send_text(data)
                        except Exception:
                            dead.append(socket)
                    for socket in dead:
                        await self.disconnect(user_id, socket)
                except (KeyError, TypeError, ValueError):
                    logger.warning("Invalid message delivery payload ignored")
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Message Redis listener cycle failed")
                await asyncio.sleep(1)

    async def _presence_loop(self):
        try:
            while True:
                try:
                    for user_id, connections in list(self.active_connections.items()):
                        for connection_id in connections.values():
                            await self._refresh_presence(user_id, connection_id)
                except Exception:
                    logger.exception("Presence refresh cycle failed")
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Presence refresh loop failed")

    async def _refresh_presence(self, user_id: str, connection_id: str):
        pipeline = database.redis.pipeline()
        pipeline.setex(f"ws_presence:{user_id}:{connection_id}", 75, "1")
        pipeline.setex(f"user_online:{user_id}", 75, "true")
        await pipeline.execute()

    async def connect(self, user_id: str, websocket: WebSocket):
        current = self.active_connections.get(user_id, {})
        remote_count = 0
        async for key in database.redis.scan_iter(
            match=f"ws_presence:{user_id}:*",
            count=20,
        ):
            remote_count += 1
            if remote_count >= settings.MAX_WS_CONNECTIONS_PER_USER:
                break
        if (
            len(current) >= settings.MAX_WS_CONNECTIONS_PER_USER
            or remote_count >= settings.MAX_WS_CONNECTIONS_PER_USER
        ):
            await websocket.close(code=1008)
            return False
        await websocket.accept(subprotocol="doclib")
        connection_id = str(uuid.uuid4())
        self.active_connections.setdefault(user_id, {})[websocket] = connection_id
        await self._refresh_presence(user_id, connection_id)
        return True

    async def disconnect(self, user_id: str, websocket: WebSocket):
        connections = self.active_connections.get(user_id)
        if not connections:
            return
        connection_id = connections.pop(websocket, None)
        if connection_id:
            await database.redis.delete(f"ws_presence:{user_id}:{connection_id}")
        if connections:
            return
        self.active_connections.pop(user_id, None)
        remaining = [
            key
            async for key in database.redis.scan_iter(
                match=f"ws_presence:{user_id}:*",
                count=20,
            )
        ]
        if not remaining:
            pipeline = database.redis.pipeline()
            pipeline.delete(f"user_online:{user_id}")
            pipeline.set(f"user_last_active:{user_id}", str(int(time.time())))
            await pipeline.execute()

    async def send_personal_message(self, message: dict, receiver_id: str):
        serialized = json.dumps(message, ensure_ascii=False, separators=(",", ":"))
        if len(serialized.encode("utf-8")) > settings.MAX_WS_MESSAGE_BYTES:
            raise ValueError("Message delivery payload is too large")
        await database.redis.publish(f"message_delivery:{receiver_id}", serialized)

    async def _allowed_contacts(self, user_id: str, requested: list[str]) -> set[str]:
        safe_ids = {
            str(value)
            for value in requested
            if isinstance(value, str)
            and 1 <= len(value) <= 128
            and value != user_id
            and not value.startswith("group_")
        }
        if not safe_ids:
            return set()
        return await allowed_contacts(user_id, list(safe_ids))

    async def handle_action(self, user_id: str, payload: dict, websocket: WebSocket):
        if not isinstance(payload, dict):
            await websocket.send_json({"type": "error", "data": {"code": "invalid_payload"}})
            return
        action = payload.get("action")
        data = payload.get("data", {})
        if action in {"typing_start", "typing_end"}:
            receiver_id = data.get("receiver_id") if isinstance(data, dict) else None
            allowed = await self._allowed_contacts(user_id, [receiver_id])
            if receiver_id not in allowed:
                await websocket.send_json({"type": "error", "data": {"code": "contact_not_allowed"}})
                return
            await self.send_personal_message(
                {
                    "type": action,
                    "data": {
                        "sender_id": user_id,
                        "receiver_id": receiver_id,
                    },
                },
                receiver_id,
            )
            return
        if action == "check_online":
            user_ids = data.get("user_ids", []) if isinstance(data, dict) else []
            if not isinstance(user_ids, list) or len(user_ids) > 100:
                await websocket.send_json({"type": "error", "data": {"code": "invalid_user_list"}})
                return
            allowed = await self._allowed_contacts(user_id, user_ids)
            status_map = {}
            for target in allowed:
                if await database.redis.exists(f"user_online:{target}"):
                    status_map[target] = True
                else:
                    last_active = await database.redis.get(f"user_last_active:{target}")
                    status_map[target] = int(last_active) if last_active else False
            await websocket.send_json({"type": "online_status", "data": status_map})
            return
        if action == "sync":
            await websocket.send_json({"type": "sync_required", "data": {}})
            return
        await websocket.send_json({"type": "error", "data": {"code": "unsupported_action"}})

    async def close(self):
        tasks = [self._listener_task, self._presence_task]
        for task in tasks:
            if task:
                task.cancel()
        for task in tasks:
            if task:
                with suppress(asyncio.CancelledError):
                    await task
        self._listener_task = None
        self._presence_task = None
        if self._pubsub:
            await self._pubsub.aclose()
            self._pubsub = None
        sockets = [
            socket
            for connections in self.active_connections.values()
            for socket in connections
        ]
        for socket in sockets:
            with suppress(Exception):
                await socket.close(code=1001)
        self.active_connections.clear()

    def is_running(self) -> bool:
        return bool(
            self._listener_task
            and not self._listener_task.done()
            and self._presence_task
            and not self._presence_task.done()
        )


message_manager = MessageSocket()
