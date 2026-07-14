from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid6 import uuid7

from fastapi import HTTPException
from src.repositories.chat import ChatRepository
from src.repositories.chat import ChatRepository

class HistoryService:
    """
    <module_purpose>
    <purpose>Manages chat history state and persistence for LLM memory.</purpose>
    <metis_behavior>Enforces absolute data integrity. Logs logic execution transparently via decorators.</metis_behavior>
    </module_purpose>
    """
    @staticmethod
    @log_logic_execution
    async def create_session(data: dict) -> Dict[str, Any]:
        user_id = data.get("user_id")
        document_id = data.get("document_id")
        first_query = data.get("first_query", "")
        if not user_id:
            raise HTTPException(
                status_code=400, detail="Yêu cầu bị từ chối do thiếu thông định danh người dùng"
            )

        title = first_query[:40] if first_query else "Cuộc trò chuyện mới"
        session = {
            "_id": str(uuid7()),
            "user_id": user_id,
            "document_id": document_id,
            "title": title,
            "messages": [],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        await ChatRepository.insert_ai_session(session)
        return session

    @staticmethod
    @log_logic_execution
    async def get_user_sessions(user_id: str, document_id: Optional[str] = None) -> List[dict]:
        query = {"user_id": user_id}
        if document_id:
            query["document_id"] = document_id
        cursor = (
            ChatRepository
            .find_ai_sessions(query, {"messages": 0})
            .sort("updated_at", -1)
        )
        return await cursor.to_list(length=None)

    @staticmethod
    @log_logic_execution
    async def get_session_detail(session_id: str, user_id: str) -> Dict[str, Any]:
        session = await ChatRepository.find_ai_session(
            {"_id": session_id, "user_id": user_id}
        )
        if not session:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy lịch sử cuộc trò chuyện yêu cầu")
        messages = await (
            ChatRepository
            .find_ai_messages({"session_id": session_id})
            .sort("created_at", 1)
            .to_list(length=None)
        )
        session["messages"] = messages
        return session

    @staticmethod
    @log_logic_execution
    async def update_title(session_id: str, data: dict, user_id: str) -> Dict[str, Any]:
        result = await ChatRepository.update_ai_session(
            {"_id": session_id, "user_id": user_id},
            {
                "$set": {
                    "title": data.get("title", ""),
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy lịch sử cuộc trò chuyện yêu cầu")
        return {"status": "success"}

    @staticmethod
    @log_logic_execution
    async def delete_session(session_id: str, user_id: str) -> Dict[str, Any]:
        result = await ChatRepository.delete_ai_session(
            {"_id": session_id, "user_id": user_id}
        )
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy lịch sử cuộc trò chuyện yêu cầu")
        return {"status": "success"}

    @staticmethod
    @log_logic_execution
    async def add_message(session_id: str, data: dict) -> Dict[str, Any]:
        user_id = data.get("user_id")
        role = data.get("role")
        content = data.get("content")
        if not user_id or not role or not content:
            raise HTTPException(status_code=400, detail="Yêu cầu bị từ chối do thiếu các thông tin bắt buộc")
        message_id = str(uuid7())
        message = {
            "_id": message_id,
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "created_at": datetime.now(timezone.utc),
        }
        await ChatRepository.insert_ai_message(message)
        await ChatRepository.update_ai_session(
            {"_id": session_id, "user_id": user_id},
            {"$set": {"updated_at": datetime.now(timezone.utc)}},
        )
        return {"status": "success"}
    @staticmethod
    @log_logic_execution
    async def search_by_keyword(user_id: str, keyword: str) -> List[Dict[str, Any]]:
        regex = {"$regex": keyword, "$options": "i"}
        matching_msgs = await (
            ChatRepository.find_ai_messages(
                {"user_id": user_id, "content": regex},
                {"session_id": 1}
            ).to_list(length=None)
        )
        session_ids = list(set([m["session_id"] for m in matching_msgs]))
        
        query = {
            "user_id": user_id,
            "$or": [
                {"title": regex},
                {"_id": {"$in": session_ids}}
            ]
        }
        cursor = ChatRepository.find_ai_sessions(query).sort("updated_at", -1).limit(10)
        return await cursor.to_list(length=None)

    @staticmethod
    @log_logic_execution
    async def get_recent_chats(user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        from datetime import timedelta
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        query = {
            "user_id": user_id,
            "updated_at": {"$gte": cutoff_date}
        }
        cursor = ChatRepository.find_ai_sessions(query).sort("updated_at", -1).limit(20)
        return await cursor.to_list(length=None)
