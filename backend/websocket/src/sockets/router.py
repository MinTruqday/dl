from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from src.core.security import get_user_id_from_token
from src.sockets.chat_manager import chat_manager
from src.sockets.editor_manager import editor_manager
from loguru import logger

router = APIRouter()

@router.websocket("/tro-chuyen/{user_id}")
async def chat_websocket(websocket: WebSocket, user_id: str, token: str = Query(...)):
    try:
        token_user_id = get_user_id_from_token(token)
        if token_user_id != user_id:
            await websocket.close(code=1008, reason="Unauthorized user")
            return
            
        await chat_manager.connect(websocket, user_id)
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        chat_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"Chat WebSocket error for {user_id}: {e}")
        chat_manager.disconnect(websocket, user_id)

@router.websocket("/editor/o-cam/{document_id}")
async def editor_websocket(websocket: WebSocket, document_id: str, token: str = Query(...)):
    try:
        user_id = get_user_id_from_token(token)
        await editor_manager.connect(websocket, document_id)
        while True:
            data = await websocket.receive_text()
            await editor_manager.broadcast_text(data, document_id, websocket)
    except WebSocketDisconnect:
        editor_manager.disconnect(websocket, document_id)
    except Exception as e:
        logger.error(f"Editor WebSocket error for {document_id}: {e}")
        editor_manager.disconnect(websocket, document_id)

@router.websocket("/editor/o-cam-dong-bo/{document_id}")
async def editor_crdt_websocket(websocket: WebSocket, document_id: str, token: str = Query(...)):
    try:
        user_id = get_user_id_from_token(token)
        await editor_manager.connect(websocket, document_id)
        while True:
            data = await websocket.receive_bytes()
            await editor_manager.broadcast_bytes(data, document_id, websocket)
    except WebSocketDisconnect:
        editor_manager.disconnect(websocket, document_id)
    except Exception as e:
        logger.error(f"Editor CRDT error for {document_id}: {e}")
        editor_manager.disconnect(websocket, document_id)
