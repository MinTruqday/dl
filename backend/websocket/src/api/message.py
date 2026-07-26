import asyncio
import json
import time
from collections import deque

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.security import authenticate_socket, session_is_active
from src.sockets.message import message_manager


router = APIRouter(prefix="/ws")


@router.websocket("/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    if not user_id or len(user_id) > 128:
        await websocket.close(code=1008)
        return
    identity = await authenticate_socket(websocket)
    if not identity or identity.user_id != user_id:
        await websocket.close(code=1008)
        return
    if not await message_manager.connect(user_id, websocket):
        return
    frame_times = deque()
    try:
        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=45)
            except asyncio.TimeoutError:
                if not await session_is_active(identity):
                    await websocket.close(code=1008)
                    return
                await websocket.send_json({"type": "heartbeat"})
                continue
            size = len(raw.encode("utf-8"))
            if size < 2 or size > 16384:
                await websocket.close(code=1009)
                return
            now = time.monotonic()
            frame_times.append(now)
            while frame_times and now - frame_times[0] > 1:
                frame_times.popleft()
            if len(frame_times) > settings.MAX_WS_FRAMES_PER_SECOND:
                await database.redis.setex(f"ws_ban:{user_id}", 300, "rate_limit")
                await websocket.close(code=1008)
                return
            if not await session_is_active(identity):
                await websocket.close(code=1008)
                return
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "data": {"code": "invalid_json"}})
                continue
            if isinstance(payload, dict) and payload.get("action") == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            await message_manager.handle_action(user_id, payload, websocket)
    except WebSocketDisconnect:
        return
    finally:
        await message_manager.disconnect(user_id, websocket)
