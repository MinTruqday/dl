from fastapi import APIRouter, HTTPException
from typing import Optional, List, Any
from loguru import logger
from src.core.config import settings
from src.models.inference import (
    GenerationRequest, TranslationRequest, SentimentRequest,
    CoverRequest, CodeRequest, GrammarRequest, FlashcardRequest,
    SummarizeRequest, ActionRequest, MindmapRequest, CitationRequest,
    ToneRequest, ReviewRequest, SynthesisRequest, PostRequest,
    StoryRequest, EngagementRequest
)
from huggingface_hub import AsyncInferenceClient
import httpx
import base64
import asyncio

router = APIRouter()

client = AsyncInferenceClient(token=settings.HF_TOKEN)

async def _chat_direct(messages: List[dict], max_tokens: int = 500, temperature: float = 0.3) -> str:
    try:
        response = await client.chat_completion(
            model=settings.LLAMA_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Inference: Model {settings.LLAMA_MODEL} failed: {e}")
        raise e

@router.post("/tao-noi-dung")
async def generate_text(req: GenerationRequest):
    try:
        result = await _chat_direct(
            messages=[{"role": "user", "content": req.prompt}],
            max_tokens=req.max_tokens,
            temperature=req.temperature
        )
        return {"result": result}
    except Exception:
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố, vui lòng thử lại sau.")

@router.post("/dich-thuat")
async def translate_text(req: TranslationRequest):
    try:
        prompt = f"Dịch đoạn văn sau sang tiếng {req.target_lang}. Chỉ trả về bản dịch, không thêm nội dung khác:\n\n{req.text}"
        result = await _chat_direct(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=len(req.text) * 3,
            temperature=0.1
        )
        return {"translation": result.strip()}
    except Exception:
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố, vui lòng thử lại sau.")

@router.post("/phan-tich-cam-xuc")
async def analyze_sentiment(req: SentimentRequest):
    try:
        texts_to_analyze = req.texts or []
        
        if req.document_id:
            from motor.motor_asyncio import AsyncIOMotorClient
            mongo_client = AsyncIOMotorClient(settings.MONGODB_URI)
            db = mongo_client.get_default_database()
            cursor = db["comments"].find({"document_id": req.document_id}, {"content": 1}).limit(20)
            comments = await cursor.to_list(length=20)
            texts_to_analyze.extend([c["content"] for c in comments if c.get("content")])
            mongo_client.close()

        if not texts_to_analyze:
            return {
                "sentiment_score": 0.0,
                "mood": "unknown",
                "summary": "Không có dữ liệu văn bản để phân tích.",
                "top_emotions": []
            }

        results = []
        for text in texts_to_analyze[:10]:
            prompt = f"Phân tích cảm xúc của đoạn văn sau. Trả lời duy nhất 1 từ (Tích cực, Tiêu cực hoặc Trung lập):\n\n{text}"
            sentiment = await _chat_direct(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.1
            )
            results.append(sentiment.strip())
        
        pos = results.count("Tích cực")
        neg = results.count("Tiêu cực")
        total = len(results)
        score = (pos - neg) / total if total > 0 else 0
        
        mood = "neutral"
        if score > 0.2: mood = "positive"
        elif score < -0.2: mood = "negative"
        
        summary_prompt = f"Dựa trên các nhận xét sau, hãy viết một câu tóm tắt cảm nhận chung của độc giả: {'; '.join(texts_to_analyze[:5])}"
        summary = await _chat_direct(
            messages=[{"role": "user", "content": summary_prompt}],
            max_tokens=100
        )

        from collections import Counter
        emotions_map = Counter(results)
        top_emotions = [{"emotion": k, "count": v} for k, v in emotions_map.most_common()]

        return {
            "sentiment_score": score,
            "mood": mood,
            "summary": summary.strip(),
            "top_emotions": top_emotions,
            "analysis": [{"text": t, "sentiment": s} for t, s in zip(texts_to_analyze, results)]
        }
    except Exception as e:
        logger.error(f"Inference: Sentiment analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố, vui lòng thử lại sau.")

@router.post("/tao-anh-bia")
async def generate_cover(req: CoverRequest):
    try:
        model_id = settings.IMAGE_GEN_MODEL
        if not model_id:
            raise HTTPException(status_code=503, detail="Mô hình tạo ảnh chưa được cấu hình")
            
        prompt = f"Book cover for {req.title}. Description: {req.description}. Style: {req.style}. High quality, cinematic."
        
        try:
            image_data = await client.text_to_image(prompt, model=model_id)
            import io
            buffered = io.BytesIO()
            image_data.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            return {
                "cover_url": f"data:image/jpeg;base64,{img_str}",
                "message": "Đã tạo ảnh bìa thành công"
            }
        except Exception as e:
            logger.error(f"Inference: Image generation failed for model {model_id}: {e}")
            return {
                "cover_url": "https://placehold.co/600x400?text=Loi+Tao+Anh",
                "message": "Gặp sự cố khi gọi mô hình tạo ảnh"
            }
    except Exception:
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố, vui lòng thử lại sau.")

@router.post("/tao-ma-nguon")
async def generate_code(req: CodeRequest):
    try:
        prompt = f"Viết mã nguồn {req.language} sạch và hiệu quả cho yêu cầu sau. Chỉ trả về khối mã:\n\n{req.prompt}"
        result = await _chat_direct(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.2
        )
        return {"code": result.strip()}
    except Exception:
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố, vui lòng thử lại sau.")

@router.post("/kiem-tra-ngu-phap")
async def grammar_check(req: GrammarRequest):
    try:
        prompt = f"Kiểm tra và sửa lỗi chính tả, ngữ pháp cho đoạn văn bản sau. Chỉ trả về đoạn văn đã sửa:\n\n{req.text}"
        result = await _chat_direct(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=len(req.text) + 200,
            temperature=0.1
        )
        import difflib
        similarity = difflib.SequenceMatcher(None, req.text, result.strip()).ratio()
        grammar_score = round(similarity * 100, 1)
        
        return {
            "corrected_text": result.strip(), 
            "score": grammar_score, 
            "message": "Đã hoàn thành kiểm tra ngữ pháp và tính toán độ chính xác."
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố, vui lòng thử lại sau.")

@router.post("/tao-the-ghi-nho")
async def generate_flashcard(req: FlashcardRequest):
    try:
        prompt = f"Dựa trên văn bản và bối cảnh sau, hãy tạo một flashcard (thẻ ghi nhớ) chất lượng cao với 2 mặt: Câu hỏi (front) và Câu trả lời (back). Trả về định dạng JSON: {{'front': '...', 'back': '...'}}.\nContext: {req.context}\nText: {req.text}"
        result = await _chat_direct(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.4
        )
        try:
            import json as json_mod
            import re
            json_match = re.search(r"\{.*\}", result, re.DOTALL)
            if json_match:
                return json_mod.loads(json_match.group())
        except:
            pass
        if ":" in result:
            parts = result.split(":", 1)
            return {"front": parts[0].strip(), "back": parts[1].strip()}
        return {"front": "Kiến thức quan trọng", "back": result.strip()}
    except Exception:
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố, vui lòng thử lại sau.")

@router.post("/tom-tat")
async def summarize_text(req: SummarizeRequest):
    try:
        prompt = f"Cung cấp một bản tóm tắt ngắn gọn, súc tích bằng tiếng {req.language} cho nội dung sau:\n\n{req.text}"
        result = await _chat_direct(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3
        )
        return {"summary": result.strip()}
    except Exception:
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố, vui lòng thử lại sau.")

@router.post("/kiem-tra-dao-van")
async def check_plagiarism(req: GrammarRequest):
    try:
        from src.ingestion.embedder import embedding_service
        from src.store.vector_store import vector_store
        
        query_vector = await embedding_service.embed_query(req.text[:2000])
        matches = await vector_store.query(query_vector=query_vector, limit=5)
        
        significant_matches = [m for m in matches if m["score"] > 0.75]
        
        if not significant_matches:
            return {
                "plagiarism_score": 0.0,
                "status": "clean",
                "message": "Không tìm thấy nội dung tương tự trong hệ thống dữ liệu hiện có. Nội dung có tính nguyên bản cao.",
                "matches": []
            }
        
        context = "\n".join([f"- Match (Score: {m['score']:.2f}): {m['text'][:200]}" for m in significant_matches])
        prompt = f"""Bạn là một Chuyên gia Kiểm định Bản quyền. 
Dưới đây là một đoạn văn bản cần kiểm tra và các đoạn văn bản tương tự tìm thấy trong hệ thống:

Văn bản cần kiểm tra:
{req.text[:1000]}

Các nội dung tương tự tìm thấy:
{context}

Nhiệm vụ của bạn:
1. Đánh giá xem sự tương đồng này là do trùng hợp ngẫu nhiên hay có dấu hiệu sao chép.
2. Tính toán một 'Plagiarism Score' (0-100).
3. Trả về kết quả duy nhất dưới dạng JSON: {{'plagiarism_score': float, 'status': 'clean|warning|danger', 'message': '...', 'matched_sources': [...]}}
"""
        result = await _chat_direct(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.1
        )
        
        try:
            import json as json_mod
            import re
            json_match = re.search(r"\{.*\}", result, re.DOTALL)
            if json_match:
                return json_mod.loads(json_match.group())
        except:
            pass
            
        max_score = max([m["score"] for m in significant_matches]) * 100
        return {
            "plagiarism_score": round(max_score, 1),
            "status": "warning" if max_score > 60 else "danger" if max_score > 85 else "clean",
            "message": "Tìm thấy nội dung có sự tương đồng đáng kể.",
            "matches": significant_matches[:3]
        }
    except Exception as e:
        logger.error(f"Inference: Real plagiarism check failed: {e}")
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố, vui lòng thử lại sau.")

@router.post("/hanh-dong")
async def unified_action(req: ActionRequest):
    try:
        prompts = {
            "autocomplete": f"Viết tiếp một câu hợp lý cho đoạn văn này mà không lặp lại nội dung cũ. Context: {req.context}. Text: {req.text}",
            "grammar": f"Sửa tất cả lỗi ngữ pháp và chính tả trong đoạn văn sau. Chỉ trả về văn bản đã sửa: {req.text}",
            "summarize": f"Tóm tắt ngắn gọn nội dung sau: {req.text}",
            "enhance_social": f"Là một chuyên gia mạng xã hội, hãy trau chuốt nội dung sau để thu hút hơn (phong cách Swiss-Brutalist: trực diện, tối giản, táo bạo). Gợi ý thêm 3-5 hashtag. Văn bản: {req.text}",
            "ai_suggestions": f"Dựa trên bối cảnh '{req.context}', hãy gợi ý 3 hướng phát triển tiếp theo cho nội dung này: {req.text}",
            "check_logic": f"Kiểm tra sự mâu thuẫn về logic, cốt truyện hoặc nhân vật trong nội dung sau, dựa trên bối cảnh: {req.context}. Nội dung: {req.text}"
        }
        
        prompt = prompts.get(req.action)
        if not prompt:
            raise HTTPException(status_code=400, detail="Hành động không hợp lệ")
            
        result = await _chat_direct(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3
        )
        return {"result": result.strip()}
    except Exception as e:
        logger.error(f"Inference: Action {req.action} failed: {e}")
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố, vui lòng thử lại sau.")

@router.post("/tu-dong-nghia")
async def get_synonyms(req: GrammarRequest):
    try:
        prompt = f"Tìm các từ đồng nghĩa cho cụm từ hoặc đoạn văn sau. Chỉ trả về danh sách phân cách bằng dấu phẩy:\n\n{req.text}"
        result = await _chat_direct(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.5
        )
        return {"synonyms": [s.strip() for s in result.split(",")]}
    except Exception:
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố, vui lòng thử lại sau.")

@router.post("/tao-ban-do-tu-duy")
async def generate_mindmap(req: MindmapRequest):
    try:
        prompt = f"Phân tích văn bản sau và tạo một bản đồ tư duy (mindmap) với độ sâu {req.depth}. Trả về ĐÚNG MỘT khối JSON hợp lệ, KHÔNG có markdown, KHÔNG có text thừa. Cấu trúc JSON: {{\"nodes\": [{{\"id\": \"root\", \"label\": \"...\"}}], \"edges\": [{{\"from\": \"root\", \"to\": \"...\"}}]}}.\n\nVăn bản: {req.text[:2000]}"
        result = await _chat_direct(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.2
        )
        try:
            import json as json_mod
            import re
            json_match = re.search(r"\{.*\}", result, re.DOTALL)
            if json_match:
                return json_mod.loads(json_match.group())
        except:
            pass
        return {"error": "Không thể tạo cấu trúc bản đồ tư duy"}
    except Exception:
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố, vui lòng thử lại sau.")

@router.post("/trich-dan-thong-minh")
async def suggest_citations(req: CitationRequest):
    try:
        from src.ingestion.embedder import embedding_service
        from src.store.vector_store import vector_store
        
        query_vector = await embedding_service.embed_query(req.text[:500])
        matches = await vector_store.query(query_vector=query_vector, limit=3)
        
        sources = []
        for m in matches:
            meta = m.get("metadata", {})
            sources.append(f"Tài liệu: {meta.get('title', 'N/A')}, Tác giả: {meta.get('author', 'N/A')}. Nội dung: {m['text'][:200]}")
            
        prompt = f"Dựa trên văn bản người dùng đang viết và các nguồn tham khảo tìm thấy, hãy gợi ý các trích dẫn theo phong cách {req.style}. Trả về danh sách các gợi ý.\n\nVăn bản: {req.text}\n\nNguồn tham khảo:\n" + "\n".join(sources)
        result = await _chat_direct(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3
        )
        return {"citations": result.strip()}
    except Exception:
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố, vui lòng thử lại sau.")

@router.post("/bien-doi-van-ban")
async def transform_tone(req: ToneRequest):
    try:
        action = "mở rộng và biến đổi" if req.expansion else "biến đổi"
        prompt = f"Hãy {action} đoạn văn bản sau sang giọng văn '{req.tone}'. Giữ nguyên ý nghĩa cốt lõi nhưng thay đổi sắc thái ngôn ngữ phù hợp:\n\n{req.text}"
        result = await _chat_direct(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000 if req.expansion else 500,
            temperature=0.4
        )
        return {"transformed_text": result.strip()}
    except Exception:
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố, vui lòng thử lại sau.")

@router.post("/tham-dinh-noi-dung")
async def peer_review(req: ReviewRequest):
    try:
        criteria_str = ", ".join(req.criteria) if req.criteria else "tính logic, độ rõ ràng, tính thuyết phục"
        prompt = f"Bạn là một chuyên gia thẩm định nội dung. Hãy đánh giá văn bản sau dựa trên các tiêu chí: {criteria_str}. Trả về một bản báo cáo chi tiết gồm Ưu điểm, Nhược điểm và Gợi ý cải thiện.\n\nVăn bản: {req.text[:3000]}"
        result = await _chat_direct(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.2
        )
        return {"review_report": result.strip()}
    except Exception:
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố, vui lòng thử lại sau.")

@router.post("/tong-hop-da-tai-lieu")
async def multi_doc_synthesis(req: SynthesisRequest):
    try:
        from src.ingestion.embedder import embedding_service
        from src.store.vector_store import vector_store
        
        query_vector = await embedding_service.embed_query(req.query)
        
        all_context = []
        for doc_id in req.document_ids:
            matches = await vector_store.query(query_vector=query_vector, document_id=doc_id, limit=3)
            for m in matches:
                all_context.append(f"[Từ tài liệu {doc_id}]: {m['text']}")
                
        prompt = f"Tổng hợp thông tin từ nhiều tài liệu khác nhau để trả lời câu hỏi: '{req.query}'.\n\nNgữ cảnh:\n" + "\n".join(all_context[:10])
        result = await _chat_direct(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.3
        )
        return {"synthesis": result.strip(), "sources_count": len(req.document_ids)}
    except Exception:
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố, vui lòng thử lại sau.")

@router.post("/tao-bai-dang-mang-xa-hoi")
async def create_social_post(req: PostRequest):
    try:
        prompt = f"Dựa trên tài liệu/nội dung sau, hãy soạn một bài đăng mạng xã hội thu hút, bao gồm cả tiêu đề, nội dung chính và các hashtag phù hợp. Văn phong cần tự nhiên và lôi cuốn:\n\nNội dung: {req.text[:2000]}\nBối cảnh: {req.context}"
        result = await _chat_direct(
            messages=[{"role": "system", "content": "Bạn là chuyên gia sáng tạo nội dung mạng xã hội."}, {"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.7
        )
        return {"post": result.strip()}
    except Exception:
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố, vui lòng thử lại sau.")

@router.post("/tao-tin-mang-xa-hoi")
async def create_social_story(req: StoryRequest):
    try:
        prompt = f"Chuyển đổi văn bản sau thành kịch bản cho chuỗi 3-5 tin (stories) ngắn gọn. Mỗi tin bao gồm nội dung hiển thị và gợi ý hình ảnh minh họa. Định dạng: Tin 1: [Nội dung] - [Hình ảnh], Tin 2: ...\n\nVăn bản: {req.text[:2000]}"
        result = await _chat_direct(
            messages=[{"role": "system", "content": "Bạn là chuyên gia thiết kế câu chuyện thị giác."}, {"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.7
        )
        return {"story": result.strip()}
    except Exception:
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố, vui lòng thử lại sau.")

@router.post("/goi-y-tuong-tac")
async def suggest_engagement(req: EngagementRequest):
    try:
        prompt = f"Phân tích bài đăng sau và gợi ý 3 cách phản hồi khác nhau (ví dụ: đặt câu hỏi, phản biện, hoặc khen ngợi). Trả về danh sách phân cách bằng dấu '|'.\n\nBài đăng: {req.content[:1500]}"
        result = await _chat_direct(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.6
        )
        options = [opt.strip() for opt in result.split("|") if opt.strip()]
        return {"suggestions": options}
    except Exception:
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố, vui lòng thử lại sau.")

