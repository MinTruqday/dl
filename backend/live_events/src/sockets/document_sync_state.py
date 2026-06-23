from typing import Dict, List

from fastapi import WebSocket
from loguru import logger


class DocumentSync:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        logger.info("Thiết bị mới đã kết nối vào không gian cộng tác")

    def disconnect(self, websocket: WebSocket, room_id: str):
        if (
            room_id in self.active_connections
            and websocket in self.active_connections[room_id]
        ):
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
            logger.info("Thiết bị đã ngắt kết nối khỏi không gian cộng tác")

    async def broadcast(self, message: bytes, room_id: str, sender: WebSocket):
        if room_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[room_id]:
                if connection != sender:
                    try:
                        await connection.send_bytes(message)
                    except Exception:
                        logger.error("Lỗi đồng bộ dữ liệu trong không gian cộng tác")
                        dead_connections.append(connection)
            for dead in dead_connections:
                self.disconnect(dead, room_id)


editor_socket_manager = DocumentSync()
