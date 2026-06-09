from fastapi import WebSocket
from typing import Dict, List
from loguru import logger
import json

class EditorManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, document_id: str):
        await websocket.accept()
        if document_id not in self.active_connections:
            self.active_connections[document_id] = []
        self.active_connections[document_id].append(websocket)
        logger.info(f"Client joined document {document_id}. Total: {len(self.active_connections[document_id])}")

    def disconnect(self, websocket: WebSocket, document_id: str):
        if document_id in self.active_connections and websocket in self.active_connections[document_id]:
            self.active_connections[document_id].remove(websocket)
            if not self.active_connections[document_id]:
                del self.active_connections[document_id]
            logger.info(f"Client left document {document_id}.")

    async def broadcast_text(self, message: str, document_id: str, sender: WebSocket):
        if document_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[document_id]:
                if connection != sender:
                    try:
                        await connection.send_text(message)
                    except Exception as e:
                        logger.warning(f"Error broadcasting text to client in {document_id}: {e}")
                        dead_connections.append(connection)
            for dead in dead_connections:
                self.disconnect(dead, document_id)

    async def broadcast_bytes(self, message: bytes, document_id: str, sender: WebSocket):
        if document_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[document_id]:
                if connection != sender:
                    try:
                        await connection.send_bytes(message)
                    except Exception as e:
                        logger.warning(f"Error broadcasting bytes to client in {document_id}: {e}")
                        dead_connections.append(connection)
            for dead in dead_connections:
                self.disconnect(dead, document_id)

editor_manager = EditorManager()
