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
from pydantic import BaseModel
import json

class BroadcastRequest(BaseModel):
    document_id: str
    message: dict

@router.post("/broadcast")
async def broadcast_message(request: BroadcastRequest):
    try:
        data = json.dumps(request.message).encode("utf-8")
        await composition_socket_manager.broadcast(data, request.document_id, None)
        return {"status": "success"}
    except Exception as e:
        logger.exception("Failed to broadcast message")
        return {"status": "error", "message": str(e)}
