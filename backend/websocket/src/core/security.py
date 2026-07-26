import hmac
from dataclasses import dataclass

import jwt
from fastapi import WebSocket

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database


@dataclass(frozen=True)
class SocketIdentity:
    user_id: str
    session_id: str
    role: str


def allowed_origin(websocket: WebSocket) -> bool:
    configured = {
        value.strip()
        for value in settings.CORS_ALLOWED_ORIGINS.split(",")
        if value.strip()
    }
    origin = websocket.headers.get("origin")
    return not configured or not origin or origin in configured


def protocol_token(websocket: WebSocket) -> str:
    values = [
        value.strip()
        for value in websocket.headers.get("sec-websocket-protocol", "").split(",")
        if value.strip()
    ]
    if len(values) != 2 or values[0] != "doclib":
        return ""
    return values[1]


async def authenticate_socket(websocket: WebSocket) -> SocketIdentity | None:
    if not allowed_origin(websocket):
        return None
    token = protocol_token(websocket)
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    user_id = str(payload.get("uid") or "")
    session_id = str(payload.get("sid") or "")
    subject = str(payload.get("sub") or "")
    if not user_id or not session_id or not subject:
        return None
    if not await database.redis.sismember(f"user_sessions:{user_id}", session_id):
        return None
    if await database.redis.exists(f"ws_ban:{user_id}"):
        return None
    return SocketIdentity(
        user_id=user_id,
        session_id=session_id,
        role=str(payload.get("role", "reader")).lower(),
    )


async def session_is_active(identity: SocketIdentity) -> bool:
    return bool(
        await database.redis.sismember(
            f"user_sessions:{identity.user_id}",
            identity.session_id,
        )
    )


def valid_internal_token(value: str) -> bool:
    return bool(
        settings.SECRET_KEY
        and value
        and hmac.compare_digest(value, settings.SECRET_KEY)
    )
