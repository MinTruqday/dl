from core.config import settings
from core.database import db_client
from fastapi import HTTPException
from datetime import datetime, timezone, timedelta
import uuid
import httpx
import json
from loguru import logger
from core.http_client import make_ai_request

class AIService:
    @staticmethod
    async def smart_search(query: str, current_user) -> list:
        from services.quota import QuotaService
        rag_url = getattr(settings, "AGENTIC_AI_URL", None)
        cache_key = f"smart_search:{query}"
        if db_client.redis:
            cached = await db_client.redis.get(cache_key)
            if cached:
                logger.info(f"AI: Smart search cache hit for '{query}'")
                return json.loads(cached)

        try:
            resp = await make_ai_request(f"{rag_url}/tro-chuyen", {
                "query": f"Tìm kiếm tài liệu liên quan đến: {query}",
                "user_id": str(current_user.id),
                "useSmart": True
            })
            result = resp.json()
            if db_client.redis:
                await db_client.redis.setex(cache_key, 300, json.dumps(result))
            await QuotaService.consume_request(str(current_user.id))
            return result
        except Exception as e:
            logger.error(f"AI: Smart search failed for '{query}': {e}")
            raise HTTPException(status_code=500, detail="Lỗi kết nối đến hệ thống trí tuệ nhân tạo.")

    @staticmethod
    async def process_text(req, current_user):
        from services.quota import QuotaService
        rag_url = getattr(settings, "AGENTIC_AI_URL", None)
        if not rag_url:
            raise HTTPException(status_code=503, detail="Cấu hình dịch vụ AI chưa hoàn tất.")

        try:
            if req.action == "translate":
                res = await make_ai_request(f"{rag_url}/inference/dich-thuat", {"text": req.text, "target_lang": req.target_lang}, timeout=30.0)
                await QuotaService.consume_request(str(current_user.id))
                return {"status": "success", "result": res.json().get("translation", "")}
            else:
                res = await make_ai_request(f"{rag_url}/inference/hanh-dong", {"action": req.action, "text": req.text, "context": req.context or ""}, timeout=30.0)
                await QuotaService.consume_request(str(current_user.id))
                return {"status": "success", "result": res.json().get("result", "")}
        except Exception as e:
            logger.error(f"AI: Text processing failed for action {req.action}: {e}")
            raise HTTPException(status_code=500, detail="Lỗi khi xử lý văn bản với AI.")

    @staticmethod
    async def generate_flashcard(document_id: str, text: str, context: str, current_user):
        from services.quota import QuotaService
        rag_url = getattr(settings, "AGENTIC_AI_URL", None)
        if not rag_url: 
            raise HTTPException(status_code=503, detail="Dịch vụ AI hiện chưa được cấu hình.")
        try:
            resp = await make_ai_request(f"{rag_url}/inference/tao-the-ghi-nho", {"text": text, "context": context})
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
            await QuotaService.consume_request(str(current_user.id))
            return data
        except Exception as e:
            logger.error(f"AI: Flashcard generation failed: {e}")
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
        logger.info(f"AI: Flashcard {card_id} reviewed by user {current_user.id} (quality: {quality})")
        return {"message": "Đã cập nhật lịch ôn tập.", "next_review": next_review.isoformat()}

    @staticmethod
    async def check_grammar(text: str) -> dict:
        rag_url = getattr(settings, "AGENTIC_AI_URL", None)
        if not rag_url:
            return {"score": 100, "message": "AI không khả dụng."}
        try:
            resp = await make_ai_request(f"{rag_url}/inference/kiem-tra-ngu-phap", {"text": text[:5000]})
            return resp.json()
        except Exception as e:
            logger.error(f"AI: Grammar check failed: {e}")
            return {"score": 100, "message": "Kiểm tra ngữ pháp hiện không khả dụng."}

    @staticmethod
    async def generate_cover(title: str, description: str, style: str) -> dict:
        rag_url = getattr(settings, "AGENTIC_AI_URL", None)
        if not rag_url:
            return {"message": "AI không khả dụng."}
        try:
            resp = await make_ai_request(f"{rag_url}/inference/tao-anh-bia", {"title": title, "description": description, "style": style}, timeout=60.0)
            return resp.json()
        except Exception as e:
            logger.error(f"AI: Cover generation failed: {e}")
            return {"message": "Dịch vụ tạo ảnh bìa hiện chưa khả dụng."}

    @staticmethod
    async def generate_code(prompt: str, language: str = "python") -> dict:
        rag_url = getattr(settings, "AGENTIC_AI_URL", None)
        if not rag_url:
            return {"message": "AI không khả dụng."}
        try:
            resp = await make_ai_request(f"{rag_url}/inference/tao-ma-nguon", {"prompt": prompt, "language": language}, timeout=60.0)
            return resp.json()
        except Exception as e:
            logger.error(f"AI: Code generation failed: {e}")
            return {"message": "Dịch vụ tạo mã nguồn hiện chưa khả dụng."}

    @staticmethod
    async def analyze_reader_sentiment(document_id: str, current_user) -> dict:
        from services.quota import QuotaService
        rag_url = getattr(settings, "AGENTIC_AI_URL", None)
        if not rag_url:
            return {"message": "Dịch vụ AI hiện chưa được cấu hình."}
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{rag_url}/inference/phan-tich-cam-xuc",
                    json={"document_id": document_id}
                )
                if resp.status_code == 200:
                    await QuotaService.consume_request(str(current_user.id))
                    return resp.json()
                
                logger.warning(f"AI: Sentiment endpoint returned {resp.status_code}")
        except Exception as e:
            logger.error(f"AI: Sentiment analysis failed for {document_id}: {e}")
            
        return {
            "sentiment_score": 0.0,
            "mood": "unknown",
            "summary": "Hệ thống đang thu thập thêm dữ liệu từ độc giả để thực hiện phân tích.",
            "top_emotions": []
        }

    @staticmethod
    async def get_ai_recommendations(limit: int = 10) -> list:
        db = db_client.mongodb.get_default_database()
        from services.document import serialize_document
        cursor = db["documents"].find({
            "status": "published", 
            "is_deleted": {"$ne": True}
        }).sort([("average_rating", -1), ("views", -1)]).limit(limit)
        documents = await cursor.to_list(length=limit)
        return [serialize_document(d) for d in documents]

    @staticmethod
    async def generate_text_completion(prompt: str, max_tokens: int = 300) -> str:
        rag_url = getattr(settings, "AGENTIC_AI_URL", None)
        if not rag_url:
            return "Dịch vụ AI hiện không khả dụng."
        try:
            resp = await make_ai_request(f"{rag_url}/inference/tao-noi-dung", {"prompt": prompt, "max_tokens": max_tokens}, timeout=60.0)
            return resp.json().get("result", "Không thể tạo nội dung vào lúc này.")
        except Exception as e:
            logger.error(f"AI: Text completion failed: {e}")
        return "Lỗi kết nối đến máy chủ AI."

    @staticmethod
    async def generate_mindmap(text: str, depth: int, current_user) -> dict:
        from services.quota import QuotaService
        rag_url = getattr(settings, "AGENTIC_AI_URL", None)
        try:
            resp = await make_ai_request(f"{rag_url}/inference/tao-ban-do-tu-duy", {"text": text, "depth": depth}, timeout=60.0)
            await QuotaService.consume_request(str(current_user.id))
            return resp.json()
        except Exception as e:
            logger.error(f"AI: Mindmap generation failed: {e}")
        return {"error": "Không thể tạo bản đồ tư duy vào lúc này."}

    @staticmethod
    async def suggest_citations(text: str, style: str, current_user) -> dict:
        from services.quota import QuotaService
        rag_url = getattr(settings, "AGENTIC_AI_URL", None)
        try:
            resp = await make_ai_request(f"{rag_url}/inference/trich-dan-thong-minh", {"text": text, "style": style}, timeout=60.0)
            await QuotaService.consume_request(str(current_user.id))
            return resp.json()
        except Exception as e:
            logger.error(f"AI: Citation suggestion failed: {e}")
        return {"error": "Không thể gợi ý trích dẫn vào lúc này."}

    @staticmethod
    async def transform_tone(text: str, tone: str, expansion: bool, current_user) -> dict:
        from services.quota import QuotaService
        rag_url = getattr(settings, "AGENTIC_AI_URL", None)
        try:
            resp = await make_ai_request(f"{rag_url}/inference/bien-doi-van-ban", {"text": text, "tone": tone, "expansion": expansion}, timeout=60.0)
            await QuotaService.consume_request(str(current_user.id))
            return resp.json()
        except Exception as e:
            logger.error(f"AI: Tone transformation failed: {e}")
        return {"error": "Không thể biến đổi văn bản vào lúc này."}

    @staticmethod
    async def peer_review(text: str, criteria: list, current_user) -> dict:
        from services.quota import QuotaService
        rag_url = getattr(settings, "AGENTIC_AI_URL", None)
        try:
            resp = await make_ai_request(f"{rag_url}/inference/tham-dinh-noi-dung", {"text": text, "criteria": criteria}, timeout=60.0)
            await QuotaService.consume_request(str(current_user.id))
            return resp.json()
        except Exception as e:
            logger.error(f"AI: Peer review failed: {e}")
        return {"error": "Không thể thẩm định nội dung vào lúc này."}

    @staticmethod
    async def multi_doc_synthesis(document_ids: list, query: str, current_user) -> dict:
        from services.quota import QuotaService
        rag_url = getattr(settings, "AGENTIC_AI_URL", None)
        try:
            resp = await make_ai_request(f"{rag_url}/inference/tong-hop-da-tai-lieu", {"document_ids": document_ids, "query": query}, timeout=60.0)
            await QuotaService.consume_request(str(current_user.id))
            return resp.json()
        except Exception as e:
            logger.error(f"AI: Multi-doc synthesis failed: {e}")
        return {"error": "Không thể tổng hợp đa tài liệu vào lúc này."}
