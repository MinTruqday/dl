from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from src.services.editor_manager import manager

router = APIRouter(prefix="/soan-thao")

@router.websocket("/o-cam/{document_id}")
async def editor_websocket(websocket: WebSocket, document_id: str):
    try:
        await manager.connect(websocket, document_id)
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data.encode("utf-8"), document_id, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, document_id)
    except Exception as e:
        logger.error(f"WebSocket/CRDT error for document {document_id}: {e}")
        manager.disconnect(websocket, document_id)

@router.websocket("/o-cam-crdt/{document_id}")
async def editor_crdt_websocket(websocket: WebSocket, document_id: str):
    try:
        await manager.connect(websocket, document_id)
        while True:
            data = await websocket.receive_bytes()
            await manager.broadcast(data, document_id, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, document_id)
    except Exception as e:
        logger.error(f"WebSocket/CRDT error for document {document_id}: {e}")
        manager.disconnect(websocket, document_id)
