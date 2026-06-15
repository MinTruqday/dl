from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from src.services.editor import editor_manager

router = APIRouter()

@router.websocket("/crdt/{document_id}")
async def handle_editor_connection(websocket: WebSocket, document_id: str):
    try:
        await editor_manager.connect(websocket, document_id)
        while True:
            data = await websocket.receive_bytes()
            await editor_manager.broadcast(data, document_id, websocket)
    except WebSocketDisconnect:
        editor_manager.disconnect(websocket, document_id)
    except Exception:
        logger.error(f"Real-time data connection failed unexpectedly while synchronizing document identifier {document_id}")
        editor_manager.disconnect(websocket, document_id)