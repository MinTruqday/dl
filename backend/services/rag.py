import httpx
import os
from typing import Dict, Any, List, Optional
from loguru import logger
from core.config import settings

class RagService:
    @staticmethod
    async def proxy_rag_chat(payload: dict, auth_header: Optional[str], current_user: Optional[Any]) -> Dict[str, Any]:
        base_url = os.getenv("AGENTIC_RAG_URL", "http://agentic-rag:8100")
        rag_url = f"{base_url}/chat"
        
        if current_user:
            payload["user_id"] = str(current_user.id)
            
        headers = {"Content-Type": "application/json"}
        if auth_header:
            headers["Authorization"] = auth_header
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(rag_url, json=payload, headers=headers, timeout=60.0)
                
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"RAG Service error: {response.status_code} - {response.text}")
                return {"answer": "Hệ thống RAG hiện đang bận, vui lòng thử lại sau.", "status": response.status_code}
        except httpx.ReadError:
            logger.error("RAG chat exception: ReadError - Service closed connection unexpectedly.")
            return {"answer": "Hệ thống AI gặp sự cố trong lúc xử lý, vui lòng thử lại sau.", "status": 503}
        except Exception as e:
            logger.error(f"RAG chat exception: {type(e).__name__} - {str(e)}")
            return {"answer": f"Lỗi kết nối tới AI: {str(e)}", "status": 500}

    @staticmethod
    async def proxy_rag_stream(payload: dict, auth_header: Optional[str], current_user: Optional[Any]) -> Any:
        from fastapi.responses import StreamingResponse
        base_url = os.getenv("AGENTIC_RAG_URL", "http://agentic-rag:8100")
        rag_url = f"{base_url}/stream"
        
        if current_user:
            payload["user_id"] = str(current_user.id)
            
        headers = {"Content-Type": "application/json"}
        if auth_header:
            headers["Authorization"] = auth_header

        async def stream_generator():
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", rag_url, json=payload, headers=headers, timeout=120.0) as response:
                    async for chunk in response.aiter_bytes():
                        yield chunk

        return StreamingResponse(stream_generator(), media_type="text/event-stream")

    @staticmethod
    async def ingest(document_id: str) -> Dict[str, Any]:
        """
        Gửi yêu cầu ingest tài liệu tới service Agentic RAG.
        """
        base_url = os.getenv("AGENTIC_RAG_URL", "http://agentic-rag:8100")
        ingest_url = f"{base_url}/ingest"
        
        payload = {"document_id": document_id}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(ingest_url, json=payload, timeout=300.0)
                
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"RAG Ingest error: {response.status_code} - {response.text}")
                return {"status": "error", "message": f"Lỗi đồng bộ AI: {response.status_code}"}
        except Exception as e:
            logger.error(f"RAG ingest exception: {e}")
            return {"status": "error", "message": str(e)}
