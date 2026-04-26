import os
import httpx
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from core.database import db_client
from loguru import logger

class RagService:
    @staticmethod
    async def proxy_rag_stream(payload, auth_header, current_user):
        base_url = os.environ.get("AGENTIC_RAG_URL")
        if not base_url:
            logger.error("AGENTIC_RAG_URL not set")
            raise HTTPException(status_code=500, detail="Lỗi cấu hình hệ thống: Không tìm thấy địa chỉ dịch vụ AI.")

        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Vui lòng đăng nhập để sử dụng tính năng Trợ lý AI."
            )

        rag_url = f"{base_url}/stream"
            
        use_pro = payload.get("usePro", False)
        if use_pro and current_user:
            db = db_client.mongodb.get_default_database()
            user_doc = await db["users"].find_one({"_id": current_user.id})
            balance = user_doc.get("wallet_balance", 0) if user_doc else 0
            ai_cost = 5
            
            if balance < ai_cost:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=f"Số dư không đủ ({balance}/{ai_cost} dl). Vui lòng nạp thêm để sử dụng tính năng AI nâng cao."
                )
                
            await db["users"].update_one(
                {"_id": current_user.id},
                {"$inc": {"wallet_balance": -ai_cost}}
            )
            logger.info(f"Deducted {ai_cost} dl from user {current_user.id} for AI Pro stream")
            
            payload["useSmart"] = True
            payload["useWeb"] = True
        else:
            payload["useSmart"] = False
            payload["useWeb"] = False
            
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header

        async def stream_generator():
            try:
                async with httpx.AsyncClient() as client:
                    async with client.stream("POST", rag_url, json=payload, headers=headers, timeout=120.0) as response:
                        if response.status_code != 200:
                            text = await response.aread()
                            yield f"event: error\ndata: {text.decode()}\n\n"
                            return
                        async for chunk in response.aiter_text():
                            yield chunk
            except Exception as e:
                logger.error(f"RAG stream error: {e}")
                yield f"event: error\ndata: {str(e)}\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")

    @staticmethod
    async def proxy_rag_chat(payload, auth_header, current_user):
        base_url = os.environ.get("AGENTIC_RAG_URL")
        if not base_url:
            logger.error("AGENTIC_RAG_URL not set")
            raise HTTPException(status_code=500, detail="Lỗi cấu hình hệ thống: Không tìm thấy địa chỉ dịch vụ AI.")
            
        use_pro = payload.get("usePro", False)
        if use_pro:
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, 
                    detail="Vui lòng đăng nhập để sử dụng tính năng AI phân tích sâu."
                )
                
            db = db_client.mongodb.get_default_database()
            user_doc = await db["users"].find_one({"_id": current_user.id})
            balance = user_doc.get("wallet_balance", 0) if user_doc else 0
            ai_cost = 5
            
            if balance < ai_cost:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=f"Số dư không đủ ({balance}/{ai_cost} dl). Vui lòng nạp thêm để sử dụng AI nâng cao."
                )
                
            await db["users"].update_one(
                {"_id": current_user.id},
                {"$inc": {"wallet_balance": -ai_cost}}
            )
            logger.info(f"Deducted {ai_cost} dl from user {current_user.id} for AI Pro chat")
            payload["useSmart"] = True
            payload["useWeb"] = True
        else:
            payload["useSmart"] = False
            payload["useWeb"] = False

        rag_url = f"{base_url}/chat"
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(rag_url, json=payload, headers=headers, timeout=60.0)
                if response.status_code != 200:
                    try:
                        err_msg = response.json().get("detail", "Lỗi dịch vụ AI nội bộ")
                        raise HTTPException(status_code=response.status_code, detail=err_msg)
                    except Exception:
                        raise HTTPException(status_code=response.status_code, detail=f"Lỗi phản hồi từ AI RAG: {response.text}")
                return response.json()
        except httpx.RequestError as e:
            logger.error(f"RAG chat connection error: {e}")
            raise HTTPException(status_code=503, detail="Dịch vụ AI hiện đang tạm ngưng để bảo trì hoặc quá tải. Vui lòng thử lại sau ít phút.")