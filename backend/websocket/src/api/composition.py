import asyncio
import json
import re
import time
from collections import deque

from fastapi import APIRouter, Header, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict, Field

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.security import (
    SocketIdentity,
    authenticate_socket,
    session_is_active,
    valid_internal_token,
)
from src.sockets.composition import composition_socket_manager
from src.core.internal_services import document_exists


router = APIRouter(prefix="/ws")
ROOM_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


async def can_edit_document(document_id: str, identity: SocketIdentity) -> bool:
    return await document_exists(document_id, identity.user_id, identity.role == "admin", True)


@router.websocket("/crdt/{document_id}")
async def editor_websocket(websocket: WebSocket, document_id: str):
    if not ROOM_PATTERN.fullmatch(document_id):
        await websocket.close(code=1008)
        return
    identity = await authenticate_socket(websocket)
    if not identity or not await can_edit_document(document_id, identity):
        await websocket.close(code=1008)
        return
    await composition_socket_manager.connect(websocket, document_id)
    frame_times = deque()
    last_access_check = time.monotonic()
    try:
        while True:
            try:
                event = await asyncio.wait_for(websocket.receive(), timeout=30)
            except asyncio.TimeoutError:
                if not await session_is_active(identity) or not await can_edit_document(
                    document_id,
                    identity,
                ):
                    await websocket.close(code=1008)
                    return
                await websocket.send_json({"type": "heartbeat"})
                continue
            if event["type"] == "websocket.disconnect":
                break
            data = event.get("text")
            is_text = data is not None
            raw = data.encode("utf-8") if is_text else event.get("bytes", b"")
            if not raw or len(raw) > settings.MAX_WS_MESSAGE_BYTES:
                await websocket.close(code=1009)
                return
            now = time.monotonic()
            frame_times.append(now)
            while frame_times and now - frame_times[0] > 1:
                frame_times.popleft()
            if len(frame_times) > settings.MAX_WS_FRAMES_PER_SECOND:
                await database.redis.setex(
                    f"ws_ban:{identity.user_id}",
                    300,
                    "rate_limit",
                )
                await websocket.close(code=1008)
                return
            if now - last_access_check >= 30:
                if not await session_is_active(identity) or not await can_edit_document(
                    document_id,
                    identity,
                ):
                    await websocket.close(code=1008)
                    return
                last_access_check = now
            await composition_socket_manager.broadcast(
                raw,
                document_id,
                websocket,
                is_text,
            )
    except WebSocketDisconnect:
        return
    finally:
        await composition_socket_manager.disconnect(websocket, document_id)


class BroadcastRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(min_length=1, max_length=128)
    message: dict


@router.post("/internal/broadcast")
async def broadcast_message(
    request: BroadcastRequest,
    x_internal_token: str = Header(default=""),
):
    if not valid_internal_token(x_internal_token):
        raise HTTPException(status_code=403, detail="Invalid internal token")
    if not ROOM_PATTERN.fullmatch(request.document_id):
        raise HTTPException(status_code=422, detail="Invalid document identifier")
    if not await document_exists(request.document_id, is_admin=True):
        raise HTTPException(status_code=404, detail="Document not found")
    raw = json.dumps(
        request.message,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    if len(raw) > settings.MAX_WS_MESSAGE_BYTES:
        raise HTTPException(status_code=413, detail="Broadcast payload is too large")
    await composition_socket_manager.broadcast(
        raw,
        request.document_id,
        None,
        True,
    )
    return {"status": "success"}
