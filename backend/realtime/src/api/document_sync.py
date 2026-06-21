from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from src.sockets.document_sync import editor_socket_manager

router = APIRouter()


@router.websocket("/crdt/{document_id}")
async def editor_websocket(websocket: WebSocket, document_id: str):
    try:
        await editor_socket_manager.connect(websocket, document_id)
        while True:
            data = await websocket.receive_bytes()
            await editor_socket_manager.broadcast(data, document_id, websocket)
    except WebSocketDisconnect:
        editor_socket_manager.disconnect(websocket, document_id)
    except Exception:
        logger.error("Lỗi kết nối dữ liệu theo thời gian thực")
        editor_socket_manager.disconnect(websocket, document_id)
