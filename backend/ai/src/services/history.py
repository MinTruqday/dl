from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from fastapi import HTTPException
from src.repositories.chat import ChatRepository


class HistoryService:
    """
    <module_purpose>
    <purpose>Manages chat history state and persistence for LLM memory.</purpose>
    <metis_behavior>Enforces absolute data integrity. Logs logic execution transparently via decorators.</metis_behavior>
    </module_purpose>
    """

    @staticmethod
    async def create_session(data: dict) -> Dict[str, Any]:
        user_id = data.get("user_id")
        document_id = data.get("document_id")
        first_query = data.get("first_query", "")
        if not user_id:
            raise HTTPException(status_code=400, detail={"code": "user_id_required"})

        title = first_query[:40]
        session = {
            "_id": str(uuid.uuid4()),
            "user_id": user_id,
            "document_id": document_id,
            "title": title,
            "title_generated": False,
            "is_pinned": False,
            "is_archived": False,
            "mode": data.get("mode", "chat"),
            "messages": [],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        await ChatRepository.insert_ai_session(session)
        return session

    @staticmethod
    async def get_user_sessions(
        user_id: str, document_id: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[dict]:
        query = {"user_id": user_id}
        if document_id:
            query["document_id"] = document_id
        cursor = (
            ChatRepository.find_ai_sessions(query, {"messages": 0})
            .sort([("is_pinned", -1), ("updated_at", -1)])
            .skip(skip)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    @staticmethod
    async def get_session_detail(session_id: str, user_id: str) -> Dict[str, Any]:
        session = await ChatRepository.find_ai_session({"_id": session_id, "user_id": user_id})
        if not session:
            raise HTTPException(status_code=404, detail={"code": "chat_session_not_found"})
        messages = await (
            ChatRepository.find_ai_messages({"session_id": session_id})
            .sort("created_at", 1)
            .limit(500)
            .to_list(length=500)
        )
        session["messages"] = messages
        return session

    @staticmethod
    async def update_title(session_id: str, data: dict, user_id: str) -> Dict[str, Any]:
        result = await ChatRepository.update_ai_session(
            {"_id": session_id, "user_id": user_id},
            {
                "$set": {
                    "title": data.get("title", ""),
                    "title_generated": True,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail={"code": "chat_session_not_found"})
        return {"status": "success"}

    @staticmethod
    async def update_state(session_id: str, data: dict, user_id: str) -> Dict[str, Any]:
        values = {
            key: bool(data[key])
            for key in ("is_pinned", "is_archived")
            if data.get(key) is not None
        }
        if not values:
            raise HTTPException(status_code=400, detail={"code": "session_state_required"})
        values["updated_at"] = datetime.now(timezone.utc)
        result = await ChatRepository.update_ai_session(
            {"_id": session_id, "user_id": user_id}, {"$set": values}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail={"code": "chat_session_not_found"})
        return {"status": "success"}

    @staticmethod
    async def generate_title(
        session_id: str, user_id: str, user_content: str, assistant_content: str
    ) -> str:
        session = await ChatRepository.find_ai_session({"_id": session_id, "user_id": user_id})
        if not session or session.get("title_generated"):
            return str((session or {}).get("title", ""))

        fallback = " ".join(user_content.split())[:60].strip() or "Cuộc trò chuyện"
        title = fallback
        try:
            import asyncio
            from langchain_core.messages import HumanMessage
            from src.utils.huggingface import create_chat_model

            prompt = (
                "Tạo một tiêu đề tiếng Việt ngắn, tối đa 8 từ, cho cuộc trò chuyện sau. "
                "Chỉ trả về tiêu đề, không dùng dấu ngoặc kép.\n"
                f"Người dùng: {user_content[:1000]}\n"
                f"Trợ lý: {assistant_content[:1000]}"
            )
            response = await asyncio.wait_for(
                create_chat_model().ainvoke([HumanMessage(content=prompt)], max_tokens=32),
                timeout=20,
            )
            candidate = " ".join(str(response.content or "").split()).strip(" \"'`#")
            if candidate:
                title = candidate[:80]
        except Exception:
            title = fallback

        await ChatRepository.update_ai_session(
            {"_id": session_id, "user_id": user_id, "title_generated": {"$ne": True}},
            {
                "$set": {
                    "title": title,
                    "title_generated": True,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        return title

    @staticmethod
    async def delete_session(session_id: str, user_id: str) -> Dict[str, Any]:
        result = await ChatRepository.delete_ai_session({"_id": session_id, "user_id": user_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail={"code": "chat_session_not_found"})
        await ChatRepository.delete_many({"session_id": session_id})
        return {"status": "success"}

    @staticmethod
    async def add_message(session_id: str, data: dict) -> Dict[str, Any]:
        user_id = data.get("user_id")
        role = data.get("role")
        content = data.get("content")
        if not user_id or not role or not content:
            raise HTTPException(status_code=400, detail={"code": "required_message_fields_missing"})
        message_id = str(uuid.uuid4())
        message = {
            "_id": message_id,
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "attachments": data.get("attachments", []),
            "created_at": datetime.now(timezone.utc),
        }
        await ChatRepository.insert_ai_message(message)
        await ChatRepository.update_ai_session(
            {"_id": session_id, "user_id": user_id},
            {"$set": {"updated_at": datetime.now(timezone.utc)}},
        )
        return {"status": "success"}

    @staticmethod
    async def search_by_keyword(user_id: str, keyword: str) -> List[Dict[str, Any]]:
        regex = {"$regex": keyword, "$options": "i"}
        matching_msgs = await ChatRepository.find_ai_messages(
            {"user_id": user_id, "content": regex}, {"session_id": 1}
        ).to_list(length=None)
        session_ids = list(set([m["session_id"] for m in matching_msgs]))

        query = {"user_id": user_id, "$or": [{"title": regex}, {"_id": {"$in": session_ids}}]}
        cursor = ChatRepository.find_ai_sessions(query).sort("updated_at", -1).limit(10)
        return await cursor.to_list(length=None)

    @staticmethod
    async def get_recent_chats(user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        from datetime import timedelta

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        query = {"user_id": user_id, "updated_at": {"$gte": cutoff_date}}
        cursor = ChatRepository.find_ai_sessions(query).sort("updated_at", -1).limit(20)
        return await cursor.to_list(length=None)
