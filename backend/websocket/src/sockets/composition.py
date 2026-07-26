import asyncio
import base64
import json
import uuid
from contextlib import suppress

from fastapi import WebSocket
from loguru import logger

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database


class CompositionSocket:
    def __init__(self):
        self.instance_id = str(uuid.uuid4())
        self.active_connections: dict[str, dict[WebSocket, str]] = {}
        self._pubsub = None
        self._listener_task = None

    async def start(self):
        if self._listener_task and not self._listener_task.done():
            return
        self._pubsub = database.redis.pubsub()
        await self._pubsub.psubscribe("composition_delivery:*")
        self._listener_task = asyncio.create_task(self._global_listener())

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
                    payload = json.loads(message["data"])
                    if payload.get("origin") == self.instance_id:
                        continue
                    channel = str(message["channel"])
                    room_id = channel.split(":", 1)[1]
                    raw = base64.b64decode(payload["data"], validate=True)
                    if len(raw) > settings.MAX_WS_MESSAGE_BYTES:
                        continue
                    await self._broadcast_local(
                        room_id,
                        raw,
                        bool(payload.get("text")),
                        None,
                    )
                except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                    logger.warning("Invalid collaboration delivery payload ignored")
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Collaboration Redis listener cycle failed")
                await asyncio.sleep(1)

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept(subprotocol="doclib")
        connection_id = str(uuid.uuid4())
        self.active_connections.setdefault(room_id, {})[websocket] = connection_id
        logger.info("Device connected to collaboration workspace")

    async def disconnect(self, websocket: WebSocket, room_id: str):
        connections = self.active_connections.get(room_id)
        if not connections:
            return
        connections.pop(websocket, None)
        if not connections:
            self.active_connections.pop(room_id, None)
        logger.info("Device disconnected from collaboration workspace")

    async def _broadcast_local(
        self,
        room_id: str,
        message: bytes,
        is_text: bool,
        sender: WebSocket | None,
    ):
        dead = []
        for connection in list(self.active_connections.get(room_id, {})):
            if connection is sender:
                continue
            try:
                if is_text:
                    await connection.send_text(message.decode("utf-8"))
                else:
                    await connection.send_bytes(message)
            except Exception:
                dead.append(connection)
        for connection in dead:
            await self.disconnect(connection, room_id)

    async def broadcast(
        self,
        message: bytes,
        room_id: str,
        sender: WebSocket | None,
        is_text: bool,
    ):
        if not message or len(message) > settings.MAX_WS_MESSAGE_BYTES:
            raise ValueError("Collaboration frame size is invalid")
        await self._broadcast_local(room_id, message, is_text, sender)
        payload = json.dumps(
            {
                "origin": self.instance_id,
                "text": is_text,
                "data": base64.b64encode(message).decode("ascii"),
            },
            separators=(",", ":"),
        )
        await database.redis.publish(f"composition_delivery:{room_id}", payload)

    async def close(self):
        if self._listener_task:
            self._listener_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._listener_task
            self._listener_task = None
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
        return bool(self._listener_task and not self._listener_task.done())


composition_socket_manager = CompositionSocket()
