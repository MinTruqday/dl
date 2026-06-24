from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid6 import uuid7

from fastapi import HTTPException
from shared.repositories.database import BaseRepository

class HistoryService:
    @staticmethod
    async def create_session(data: dict) -> Dict[str, Any]:
        user_id = data.get("user_id")
        document_id = data.get("document_id")
        first_query = data.get("first_query", "")
        if not user_id:
            raise HTTPException(
                status_code=400, detail="Dữ liệu thiếu thông tin người dùng"
            )

        title = first_query[:40] if first_query else "New conversation"
        session = {
            "_id": str(uuid7()),
            "user_id": user_id,
            "document_id": document_id,
            "title": title,
            "messages": [],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        await BaseRepository.get("ai_sessions").insert_one(session)
        return session

    @staticmethod
    async def get_user_sessions(user_id: str, document_id: Optional[str] = None) -> List[dict]:
        query = {"user_id": user_id}
        if document_id:
            query["document_id"] = document_id
        cursor = (
            BaseRepository.get("ai_sessions")
            .find(query, {"messages": 0})
            .sort("updated_at", -1)
        )
        return await cursor.to_list(length=50)

    @staticmethod
    async def get_session_detail(session_id: str, user_id: str) -> Dict[str, Any]:
        session = await BaseRepository.get("ai_sessions").find_one(
            {"_id": session_id, "user_id": user_id}
        )
        if not session:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc trò chuyện")
        messages = (
            await BaseRepository.get("ai_messages")
            .find({"session_id": session_id})
            .sort("created_at", 1)
            .to_list(length=100)
        )
        session["messages"] = messages
        return session

    @staticmethod
    async def update_title(session_id: str, data: dict, user_id: str) -> Dict[str, Any]:
        result = await BaseRepository.get("ai_sessions").update_one(
            {"_id": session_id, "user_id": user_id},
            {
                "$set": {
                    "title": data.get("title", ""),
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc trò chuyện")
        return {"status": "success"}

    @staticmethod
    async def delete_session(session_id: str, user_id: str) -> Dict[str, Any]:
        result = await BaseRepository.get("ai_sessions").delete_one(
            {"_id": session_id, "user_id": user_id}
        )
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc trò chuyện")
        return {"status": "success"}

    @staticmethod
    async def add_message(session_id: str, data: dict) -> Dict[str, Any]:
        user_id = data.get("user_id")
        role = data.get("role")
        content = data.get("content")
        if not user_id or not role or not content:
            raise HTTPException(status_code=400, detail="Dữ liệu thiếu thông tin bắt buộc")
        message_id = str(uuid7())
        message = {
            "_id": message_id,
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "created_at": datetime.now(timezone.utc),
        }
        await BaseRepository.get("ai_messages").insert_one(message)
        await BaseRepository.get("ai_sessions").update_one(
            {"_id": session_id, "user_id": user_id},
            {"$set": {"updated_at": datetime.now(timezone.utc)}},
        )
        return {"status": "success"}
