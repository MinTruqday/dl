import httpx
import os
import uuid
from typing import Dict, Any, List, Optional
from loguru import logger
from core.config import settings
class RagService:
    @staticmethod
    async def proxy_rag_chat(payload: dict, auth_header: Optional[str], current_user: Optional[Any]) -> Dict[str, Any]:
        base_url = settings.AGENTIC_RAG_URL
        rag_url = f"{base_url}/chat"
        if current_user:
            payload["user_id"] = str(current_user.id)
        else:
            payload["user_id"] = f"guest_{uuid.uuid4().hex[:8]}"
        headers = {"Content-Type": "application/json"}
        if auth_header:
            headers["Authorization"] = auth_header
        try:
            session_id = payload.get("session_id")
            user_query = payload.get("query", "")
            async with httpx.AsyncClient() as client:
                response = await client.post(rag_url, json=payload, headers=headers, timeout=60.0)
            if response.status_code == 200:
                result = response.json()
                if session_id and current_user:
                    await RagService.add_message(session_id, "user", user_query, str(current_user.id))
                    await RagService.add_message(session_id, "assistant", result.get("answer", ""), str(current_user.id))
                return result
            else:
                logger.error(f"RAG Service error: {response.status_code} - {response.text}")
                return {"answer": "Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.", "status": response.status_code}
        except httpx.ReadError:
            logger.error("RAG chat exception: ReadError - Service closed connection unexpectedly.")
            return {"answer": "Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.", "status": 503}
        except Exception as e:
            logger.error(f"RAG chat exception: {type(e).__name__} - {str(e)}")
            return {"answer": "Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.", "status": 500}
    @staticmethod
    async def proxy_rag_stream(payload: dict, auth_header: Optional[str], current_user: Optional[Any]) -> Any:
        from fastapi.responses import StreamingResponse
        base_url = settings.AGENTIC_RAG_URL
        rag_url = f"{base_url}/stream"
        if current_user:
            payload["user_id"] = str(current_user.id)
        else:
            payload["user_id"] = f"guest_{uuid.uuid4().hex[:8]}"
        headers = {"Content-Type": "application/json"}
        if auth_header:
            headers["Authorization"] = auth_header
        async def stream_generator():
            import json as json_mod
            full_response = ""
            try:
                session_id = payload.get("session_id")
                user_query = payload.get("query", "")
                if session_id and current_user:
                    await RagService.add_message(session_id, "user", user_query, str(current_user.id))
                async with httpx.AsyncClient() as client:
                    async with client.stream("POST", rag_url, json=payload, headers=headers, timeout=120.0) as response:
                        if response.status_code != 200:
                            logger.error(f"RAG Stream error: {response.status_code}")
                            yield f'data: {{"error": "Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau."}}\n\n'.encode('utf-8')
                            return
                        async for chunk in response.aiter_bytes():
                            chunk_str = chunk.decode('utf-8')
                            lines = chunk_str.split("\n\n")
                            for line in lines:
                                if line.startswith("data: "):
                                    try:
                                        data = line.replace("data: ", "").strip()
                                        if data != "[DONE]":
                                            parsed = json_mod.loads(data)
                                            if "chunk" in parsed:
                                                full_response += parsed["chunk"]
                                    except Exception as parse_error:
                                        logger.warning(f"Failed to parse RAG stream chunk: {parse_error}")
                            yield chunk
                if session_id and current_user and full_response:
                    await RagService.add_message(session_id, "assistant", full_response, str(current_user.id))
            except Exception as e:
                logger.error(f"RAG stream exception: {str(e)}")
                yield f'data: {{"error": "Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau."}}\n\n'.encode('utf-8')
        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    @staticmethod
    async def ingest(document_id: str) -> Dict[str, Any]:
        base_url = settings.AGENTIC_RAG_URL
        ingest_url = f"{base_url}/ingest"
        payload = {"document_id": document_id}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(ingest_url, json=payload, timeout=300.0)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"RAG Ingest error: {response.status_code} - {response.text}")
                return {"status": "error", "message": "Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau."}
        except Exception as e:
            logger.error(f"RAG ingest exception: {e}")
            return {"status": "error", "message": "Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau."}
    @staticmethod
    async def create_session(user_id: str, document_id: Optional[str] = None, first_query: str = "") -> dict:
        from core.database import db_client
        from datetime import datetime
        db = db_client.mongodb.get_default_database()
        title = first_query[:40] if first_query else "Cuộc hội thoại mới"
        session = {
            "_id": str(uuid.uuid4()),
            "user_id": user_id,
            "document_id": document_id,
            "title": title,
            "messages": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await db["ai_sessions"].insert_one(session)
        return session
    @staticmethod
    async def get_user_sessions(user_id: str, document_id: Optional[str] = None) -> List[dict]:
        from core.database import db_client
        db = db_client.mongodb.get_default_database()
        query = {"user_id": user_id}
        if document_id: query["document_id"] = document_id
        cursor = db["ai_sessions"].find(query).sort("updated_at", -1)
        return await cursor.to_list(length=50)
    @staticmethod
    async def add_message(session_id: str, role: str, content: str, user_id: str) -> bool:
        from core.database import db_client
        from datetime import datetime
        db = db_client.mongodb.get_default_database()
        message = {"id": str(uuid.uuid4()), "role": role, "content": content, "created_at": datetime.utcnow()}
        result = await db["ai_sessions"].update_one(
            {"_id": session_id, "user_id": user_id},
            {"$push": {"messages": message}, "$set": {"updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    @staticmethod
    async def delete_session(session_id: str, user_id: str) -> bool:
        from core.database import db_client
        db = db_client.mongodb.get_default_database()
        result = await db["ai_sessions"].delete_one({"_id": session_id, "user_id": user_id})
        return result.deleted_count > 0
    @staticmethod
    async def update_title(session_id: str, title: str, user_id: str) -> bool:
        from core.database import db_client
        from datetime import datetime
        db = db_client.mongodb.get_default_database()
        result = await db["ai_sessions"].update_one(
            {"_id": session_id, "user_id": user_id},
            {"$set": {"title": title, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
