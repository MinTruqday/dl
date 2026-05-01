from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger
from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from bson import ObjectId
from core.database import db_client
import os
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        logger.info(f"Client joined room {room_id}. Total: {len(self.active_connections[room_id])}")

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections and websocket in self.active_connections[room_id]:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
            logger.info(f"Client left room {room_id}")

    async def broadcast(self, message: bytes, room_id: str, sender: WebSocket):
        if room_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[room_id]:
                if connection != sender:
                    try:
                        await connection.send_bytes(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to client in {room_id}: {e}")
                        dead_connections.append(connection)
            for dead in dead_connections:
                self.disconnect(dead, room_id)

manager = ConnectionManager()

class EditorService:
    @staticmethod
    async def analyze_internal_plagiarism(document_id: str, content_payload: dict, current_user):
        content = content_payload.get("content", "")
        if not content or len(content.split()) < 10:
            return {"duplication_score": 0.0, "status": "clean"}
        try:
            db = db_client.mongodb.get_default_database()
            documents = await db["documents"].find({"$text": {"$search": content[:100]}}).limit(1).to_list(1)
            if documents and str(documents[0]["_id"]) != document_id:
                return {
                    "duplication_score": 85.5,
                    "matched_with": documents[0].get("title", "Tài liệu không xác định"),
                    "status": "warning"
                }
            return {"duplication_score": 0.0, "status": "clean"}
        except Exception as e:
            logger.error(f"Plagiarism check error: {e}")
            return {"duplication_score": 0.0, "status": "clean", "error": str(e)}

    @staticmethod
    async def sync_keystroke_buffer(document_id: str, payload: dict, current_user):
        try:
            if db_client.redis:
                user_id = str(current_user.id)
                await db_client.redis.publish(f"editor:{document_id}:keystroke", str(payload))
                await db_client.redis.hset(
                    f"editor_snapshot:{document_id}",
                    user_id,
                    str(payload)
                )
            return {"status": "synced_redis", "timestamp": payload.get("timestamp")}
        except Exception as e:
            logger.error(f"Error syncing keystrokes: {e}")
            return {"status": "sync_failed", "error": str(e)}

    @staticmethod
    async def get_latex():
        from api.latex_data import LATEX_COMMANDS, LATEX_PACKAGES, LATEX_ENVIRONMENTS
        return {
            "commands": LATEX_COMMANDS,
            "packages": LATEX_PACKAGES,
            "environments": LATEX_ENVIRONMENTS
        }

    @staticmethod
    async def add_inline_suggestion(document_id: str, payload: dict, current_user):
        db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        await db["editor_suggestions"].insert_one({
            "document_id": str(document_id),
            "reviewer_id": user_id,
            "selected_text": payload.get("selected_text"),
            "suggested_text": payload.get("suggested_text"),
            "comment": payload.get("comment"),
            "status": "pending",
            "created_at": datetime.utcnow()
        })
        logger.info(f"Inline suggestion added for document {document_id} by user {user_id}")
        return {"message": "Đã thêm gợi ý chỉnh sửa thành công."}

    @staticmethod
    async def resolve_suggestion(suggestion_id: str, payload: dict, current_user):
        db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        sug = await db["editor_suggestions"].find_one({"_id": ObjectId(suggestion_id)})
        if not sug: 
            raise HTTPException(status_code=404, detail="Không tìm thấy gợi ý.")
        await db["editor_suggestions"].update_one({"_id": ObjectId(suggestion_id)}, {"$set": {
            "status": payload.get("action", "rejected"),
            "resolved_at": datetime.utcnow()
        }})
        logger.info(f"Suggestion {suggestion_id} resolved by user {user_id}")
        action_map = {"accepted": "chấp nhận", "rejected": "từ chối"}
        action_vn = action_map.get(payload.get('action'), payload.get('action'))
        return {"message": f"Đã {action_vn} gợi ý thành công."}

    @staticmethod
    async def sync_pomodoro_session(payload: dict, current_user):
        db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        await db["pomodoro_sessions"].insert_one({
            "user_id": user_id,
            "document_id": str(payload.get("document_id")),
            "duration_minutes": payload.get("duration"),
            "words_written": payload.get("words_written"),
            "created_at": datetime.utcnow()
        })
        logger.info(f"Pomodoro session recorded for user {user_id}")
        return {"status": "recorded"}

    @staticmethod
    async def auto_save_draft(document_id: str, content: dict, current_user):
        db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        await db["documents"].update_one(
            {"_id": document_id, "$or": [{"author_id": user_id}, {"co_authors": user_id}]},
            {"$set": {"draft_content": content, "updated_at": datetime.utcnow()}}
        )
        return {"message": "Tự động lưu bản nháp thành công.", "timestamp": str(datetime.utcnow())}

    @staticmethod
    async def submit_for_review(document_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        await db["documents"].update_one(
            {"_id": document_id, "author_id": user_id},
            {"$set": {"editor_review_status": "pending_review"}}
        )
        logger.info(f"Document {document_id} submitted for review by user {user_id}")
        return {"message": "Tài liệu đã được gửi và đang chờ kiểm duyệt."}

    @staticmethod
    async def global_find_replace(document_id: str, search_term: str, replace_term: str, match_case: bool, current_user):
        import re
        db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        
        document = await db["documents"].find_one({"_id": str(document_id), "author_id": user_id})
        if not document:
            raise HTTPException(status_code=403, detail="Không có quyền thao tác hoặc tài liệu không tồn tại")
            
        flags = 0 if match_case else re.IGNORECASE
        pattern = re.compile(re.escape(search_term), flags=flags)
        
        new_title = pattern.sub(replace_term, document.get("title", ""))
        new_desc = pattern.sub(replace_term, document.get("description", ""))
        
        new_content = None
        if document.get("content"):
            content_str = json.dumps(document["content"])
            new_content_str = pattern.sub(replace_term, content_str)
            try:
                new_content = json.loads(new_content_str)
            except Exception as e:
                logger.error(f"Regex JSON load failed for globally replacing content: {e}")
                new_content = None
                
        update_data = {
            "title": new_title,
            "description": new_desc,
            "updated_at": datetime.utcnow()
        }
        if new_content:
            update_data["content"] = new_content
            
        await db["documents"].update_one({"_id": str(document_id)}, {"$set": update_data})
        
        await db["document_versions"].insert_one({
            "document_id": str(document_id),
            "author_id": user_id,
            "action": "GLOBAL_REPLACE",
            "details": f"Replaced '{search_term}' with '{replace_term}'",
            "created_at": datetime.utcnow()
        })
        logger.info(f"Global find/replace executed for document {document_id} by user {user_id}")
        return {"message": "Thay thế nội dung toàn cục thành công.", "affected_fields": ["title", "description", "content"]}

    @staticmethod
    async def check_grammar(document_id: str, chapter_id: str, current_user) -> dict:
        from services.ai_assistant import AIAssistantService
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc: 
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
            
        chapter = next((ch for ch in doc.get("chapters", []) if ch.get("id") == chapter_id), None)
        if not chapter: 
            raise HTTPException(status_code=404, detail="Chương không tồn tại.")
            
        return await AIAssistantService.check_grammar(chapter.get("content", ""))

    @staticmethod
    async def generate_cover(document_id: str, style: str, current_user) -> dict:
        from services.ai_assistant import AIAssistantService
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc: 
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
            
        data = await AIAssistantService.generate_cover(doc.get("title", ""), doc.get("description", ""), style)
        if data.get("cover_url"):
            await db["documents"].update_one({"_id": document_id}, {"$set": {"cover_url": data["cover_url"], "updated_at": datetime.utcnow()}})
            logger.info(f"Workspace: Cover generated for {document_id}")
        return data
