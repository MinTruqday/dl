from typing import Dict, List

from fastapi import WebSocket
from loguru import logger


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        logger.info(
            f"A device connected to room {room_id}. Total connections: {len(self.active_connections[room_id])}"
        )

    def disconnect(self, websocket: WebSocket, room_id: str):
        if (
            room_id in self.active_connections
            and websocket in self.active_connections[room_id]
        ):
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
            logger.info(f"A device disconnected from room {room_id}")

    async def broadcast(self, message: bytes, room_id: str, sender: WebSocket):
        if room_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[room_id]:
                if connection != sender:
                    try:
                        await connection.send_bytes(message)
                    except Exception as e:
                        logger.error(f"Failed to broadcast signal to room {room_id}")
                        dead_connections.append(connection)
            for dead in dead_connections:
                self.disconnect(dead, room_id)


manager = ConnectionManager()
