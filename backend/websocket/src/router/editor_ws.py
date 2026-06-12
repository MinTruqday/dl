from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from src.services.editor_ws import manager

router = APIRouter()

@router.websocket('/ws-crdt/{document_id}')
async def editor_websocket(websocket: WebSocket, document_id: str):
    try:
        await manager.connect(websocket, document_id)
        while True:
            data = await websocket.receive_bytes()
            await manager.broadcast(data, document_id, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, document_id)
    except Exception as e:
        logger.error(f'Kết nối dữ liệu thời gian thực cho tài liệu {document_id} bị gián đoạn: {e}')
        manager.disconnect(websocket, document_id)
