from core.config import settings
from core.database import db_client
from fastapi import HTTPException
from datetime import datetime, timezone, timedelta
import uuid
import httpx
import json
from loguru import logger

class AIService:
    @staticmethod
    async def semantic_search(query: str, current_user) -> list:
        rag_url = getattr(settings, "AGENTIC_RAG_URL", None)
        if not rag_url: 
            raise HTTPException(status_code=503, detail="Dịch vụ AI chưa được cấu hình.")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(f"{rag_url}/chat", json={
                    "query": f"Tìm kiếm tài liệu liên quan đến: {query}",
                    "user_id": str(current_user.id),
                    "useSmart": True
                })
                if resp.status_code == 200:
                    return resp.json()
                raise HTTPException(status_code=resp.status_code, detail="Dịch vụ AI phản hồi không chính xác.")
        except Exception as e:
logger.info("Log message sanitized"))
            raise HTTPException(status_code=500, detail="Lỗi kết nối đến hệ thống trí tuệ nhân tạo.")

    @staticmethod
    async def process_text(req):
        rag_url = getattr(settings, "AGENTIC_RAG_URL", None)
        if not rag_url:
            raise HTTPException(status_code=503, detail="Cấu hình dịch vụ AI chưa hoàn tất.")

        try:
            async with httpx.AsyncClient() as client:
                if req.action == "translate":
                    res = await client.post(
                        f"{rag_url}/inference/translate",
                        json={"text": req.text, "target_lang": req.target_lang},
                        timeout=30.0
                    )
                    res.raise_for_status()
                    return {"status": "success", "result": res.json().get("translation", "")}
                else:
                    prompt = ""
                    if req.action == "autocomplete":
                        prompt = f"Write the next reasonable sentence for this text without echoing my text. Context: {req.context}. Text: {req.text}"
                    elif req.action == "grammar":
                        prompt = f"Fix all grammar and spelling mistakes in the following text. Only return the corrected text: {req.text}"
                    elif req.action == "summarize":
                        prompt = f"Provide a clean, concise summary of the following text: {req.text}"
                    elif req.action == "enhance_social":
                        prompt = f"As a professional social media manager, polish the following content to be more engaging and editorial (Swiss-Brutalist style: direct, minimal, bold). Also suggest 3-5 relevant hashtags. Only return the polished text and hashtags. Text: {req.text}"
                    else:
                        raise HTTPException(status_code=400, detail="Hành động không hợp lệ.")

                    res = await client.post(
                        f"{rag_url}/inference/generate",
                        json={"prompt": prompt, "max_tokens": 150},
                        timeout=30.0
                    )
                    res.raise_for_status()
                    return {"status": "success", "result": res.json().get("result", "")}
        except Exception as e:
logger.info("Log message sanitized"))
            raise HTTPException(status_code=500, detail="Lỗi khi xử lý văn bản với AI.")

    @staticmethod
    async def generate_flashcard(document_id: str, text: str, context: str, current_user):
        rag_url = getattr(settings, "AGENTIC_RAG_URL", None)
        if not rag_url: 
            raise HTTPException(status_code=503, detail="Dịch vụ AI hiện chưa được cấu hình.")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(f"{rag_url}/inference/generate-flashcard", json={"text": text, "context": context})
                if resp.status_code == 200:
                    data = resp.json()
                    db = db_client.mongodb.get_default_database()
                    flashcard = {
                        "_id": str(uuid.uuid4()), 
                        "user_id": str(current_user.id), 
                        "document_id": document_id, 
                        "front": data.get("front"), 
                        "back": data.get("back"), 
                        "created_at": datetime.now(timezone.utc)
                    }
                    await db["flashcards"].insert_one(flashcard)
                    return data
                raise HTTPException(status_code=resp.status_code, detail="AI không thể tạo thẻ ghi nhớ.")
        except Exception as e:
logger.info("Log message sanitized"))
            raise HTTPException(status_code=500, detail="Không thể kết nối đến dịch vụ AI.")
            
    @staticmethod
    async def review_flashcard(card_id: str, quality: int, current_user):
        import math
        db = db_client.mongodb.get_default_database()
        card = await db["flashcards"].find_one({"_id": card_id, "user_id": str(current_user.id)})
        if not card:
            raise HTTPException(status_code=404, detail="Không tìm thấy flashcard.")
            
        rep = card.get("repetitions", 0)
        ef = card.get("easiness_factor", 2.5)
        interval = card.get("interval", 1)
        
        if quality >= 3:
            if rep == 0: interval = 1
            elif rep == 1: interval = 6
            else: interval = math.ceil(interval * ef)
            rep += 1
        else:
            rep = 0
            interval = 1
            
        ef = max(1.3, ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
        next_review = datetime.now(timezone.utc) + timedelta(days=interval)
        
        await db["flashcards"].update_one(
            {"_id": card_id},
            {"$set": {"repetitions": rep, "easiness_factor": ef, "interval": interval, "next_review": next_review}}
        )
logger.info("Log message sanitized"))
        return {"message": "Đã cập nhật lịch ôn tập.", "next_review": next_review.isoformat()}

    @staticmethod
    async def check_grammar(text: str) -> dict:
        rag_url = getattr(settings, "AGENTIC_RAG_URL", None)
        if not rag_url:
            return {"score": 100, "message": "AI không khả dụng."}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(f"{rag_url}/inference/grammar-check", json={"text": text[:5000]})
                if resp.status_code == 200: 
                    return resp.json()
        except Exception as e:
logger.info("Log message sanitized"))
        return {"score": 100, "message": "Kiểm tra ngữ pháp hiện không khả dụng."}

    @staticmethod
    async def generate_cover(title: str, description: str, style: str) -> dict:
        rag_url = getattr(settings, "AGENTIC_RAG_URL", None)
        if not rag_url:
            return {"message": "AI không khả dụng."}
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{rag_url}/inference/generate-cover", json={"title": title, "description": description, "style": style})
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
logger.info("Log message sanitized"))
        return {"message": "Dịch vụ tạo ảnh bìa hiện chưa khả dụng."}

    @staticmethod
    async def generate_code(prompt: str, language: str = "python") -> dict:
        rag_url = getattr(settings, "AGENTIC_RAG_URL", None)
        if not rag_url:
            return {"message": "AI không khả dụng."}
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{rag_url}/inference/generate-code", json={"prompt": prompt, "language": language})
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
logger.info("Log message sanitized"))
        return {"message": "Dịch vụ tạo mã nguồn hiện chưa khả dụng."}
