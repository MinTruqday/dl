from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from loguru import logger
import json
import asyncio
import time
import jwt
from core.config import settings
from src.services.message_ws import message_manager
from src.core.database import db_client

router = APIRouter()

@router.websocket('/ws/{user_id}')
async def websocket_endpoint(websocket: WebSocket, user_id: str, token: str = Query(None)):
    if not token:
        await websocket.close(code=1008)
        return

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("sub") != user_id:
            logger.warning(f"WS Token validation failed: sub {payload.get('sub')} != {user_id}")
            await websocket.close(code=1008)
            return
    except Exception as e:
        logger.error(f"WS Token validation error for {user_id}: {e}")
        await websocket.close(code=1008)
        return

    db = db_client.redis
    if db:
        is_banned = await db.get(f'ws_ban:{user_id}')
        if is_banned:
            await websocket.close(code=1008)
            return

    await message_manager.connect(user_id, websocket)
    frame_times = []
    
    try:
        while True:
            raw = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
            now = time.time()
            frame_times.append(now)
            frame_times = [t for t in frame_times if now - t <= 1.0]
            if len(frame_times) > 5:
                if db:
                    await db.setex(f'ws_ban:{user_id}', 300, 'banned')
                message_manager.disconnect(user_id, websocket)
                await websocket.close(code=1008)
                return
            try:
                payload = json.loads(raw)
                if payload.get('action') == 'ping':
                    await websocket.send_json({'type': 'pong'})
                    continue
                await message_manager._handle_ws_action(user_id, payload)
            except json.JSONDecodeError:
                pass
    except asyncio.TimeoutError:
        message_manager.disconnect(user_id, websocket)
        try:
            await websocket.close(code=1000)
        except Exception:
            pass
    except WebSocketDisconnect:
        message_manager.disconnect(user_id, websocket)
    except Exception as e:
        logger.error(f"Message WS error for {user_id}: {e}")
        message_manager.disconnect(user_id, websocket)
