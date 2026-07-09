from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from src.sockets.composition import composition_socket_manager

router = APIRouter(route_class=LoggingRoute, prefix="/ws")

@router.websocket("/crdt/{document_id}")
async def editor_websocket(websocket: WebSocket, document_id: str):
    try:
        await composition_socket_manager.connect(websocket, document_id)
        while True:
            data = await websocket.receive_bytes()
            await composition_socket_manager.broadcast(data, document_id, websocket)
    except WebSocketDisconnect:
        composition_socket_manager.disconnect(websocket, document_id)
    except Exception as e:
        logger.exception("CRDT real-time connection setup failed")
        composition_socket_manager.disconnect(websocket, document_id)
