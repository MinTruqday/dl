from fastapi import APIRouter, HTTPException
from typing import Optional, List, Any
from loguru import logger
from src.core.config import settings
from src.schemas.inference import (
    GenerationRequest, TranslationRequest, SentimentRequest,
    CoverRequest, CodeRequest, GrammarRequest,
    SummarizeRequest, ActionRequest, CitationRequest,
    ToneRequest, ReviewRequest, SynthesisRequest
)
from huggingface_hub import AsyncInferenceClient
import httpx
import base64
import asyncio
from src.core.prompt_registry import prompt_registry, PromptType

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
        prompt = prompt_registry.get(PromptType.TRANSLATE).format(target_lang=req.target_lang, text=req.text)
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
            prompt = prompt_registry.get(PromptType.SENTIMENT_ANALYSIS).format(text=text)
            sentiment = await _chat_direct(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.1
            )
            results.append(sentiment.strip())
        
        pos = sum(1 for r in results if r.lower() in ["positive", "tích cực"])
        neg = sum(1 for r in results if r.lower() in ["negative", "tiêu cực"])
        total = len(results)
        score = (pos - neg) / total if total > 0 else 0
        
        mood = "neutral"
        if score > 0.2: mood = "positive"
        elif score < -0.2: mood = "negative"
        
        summary_prompt = prompt_registry.get(PromptType.SENTIMENT_SUMMARY).format(reviews="; ".join(texts_to_analyze[:5]))
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
            
        prompt = prompt_registry.get(PromptType.IMAGE_COVER).format(title=req.title, description=req.description, style=req.style)
        
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
        prompt = prompt_registry.get(PromptType.CODE_GENERATION).format(language=req.language, prompt=req.prompt)
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
        prompt = prompt_registry.get(PromptType.GRAMMAR_CHECK).format(text=req.text)
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


@router.post("/tom-tat")
async def summarize_text(req: SummarizeRequest):
    try:
        prompt = prompt_registry.get(PromptType.SUMMARIZE).format(language=req.language, text=req.text)
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
        from src.rag.embedder import embedding_service
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
        prompt = prompt_registry.get(PromptType.PLAGIARISM_DETECTION).format(text=req.text[:1000], context=context)
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
        except Exception as err:
            logger.warning(f"Failed to parse JSON for plagiarism check: {err}")
            
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
            "autocomplete": prompt_registry.get(PromptType.AUTOCOMPLETE).format(context=req.context, text=req.text),
            "grammar": prompt_registry.get(PromptType.GRAMMAR_CHECK).format(text=req.text),
            "summarize": prompt_registry.get(PromptType.SUMMARIZE).format(language="the input language", text=req.text),
            "ai_suggestions": prompt_registry.get(PromptType.AI_SUGGESTIONS).format(context=req.context, text=req.text),
            "check_logic": prompt_registry.get(PromptType.CHECK_LOGIC).format(context=req.context, text=req.text)
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
        prompt = prompt_registry.get(PromptType.SYNONYMS).format(text=req.text)
        result = await _chat_direct(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.5
        )
        return {"synonyms": [s.strip() for s in result.split(",")]}
    except Exception:
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố, vui lòng thử lại sau.")


@router.post("/trich-dan-thong-minh")
async def suggest_citations(req: CitationRequest):
    try:
        from src.rag.embedder import embedding_service
        from src.store.vector_store import vector_store
        
        query_vector = await embedding_service.embed_query(req.text[:500])
        matches = await vector_store.query(query_vector=query_vector, limit=3)
        
        sources = []
        for m in matches:
            meta = m.get("metadata", {})
            sources.append(f"Document: {meta.get('title', 'N/A')}, Author: {meta.get('author', 'N/A')}. Content: {m['text'][:200]}")
            
        prompt = prompt_registry.get(PromptType.SUGGEST_CITATIONS).format(style=req.style, text=req.text, sources="\\n".join(sources))
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
        action = "expand and transform" if req.expansion else "transform"
        prompt = prompt_registry.get(PromptType.TRANSFORM_TONE).format(action=action.capitalize(), tone=req.tone, text=req.text)
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
        criteria_str = ", ".join(req.criteria) if req.criteria else "logic, clarity, persuasiveness"
        prompt = prompt_registry.get(PromptType.CONTENT_REVIEW).format(criteria_str=criteria_str, text=req.text[:3000])
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
        from src.rag.embedder import embedding_service
        from src.store.vector_store import vector_store
        
        query_vector = await embedding_service.embed_query(req.query)
        
        all_context = []
        for doc_id in req.document_ids:
            matches = await vector_store.query(query_vector=query_vector, document_id=doc_id, limit=3)
            for m in matches:
                all_context.append(f"[Từ tài liệu {doc_id}]: {m['text']}")
                
        prompt = prompt_registry.get(PromptType.MULTI_DOC_SYNTHESIS).format(query=req.query, context="\\n".join(all_context[:10]))
        result = await _chat_direct(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.3
        )
        return {"synthesis": result.strip(), "sources_count": len(req.document_ids)}
    except Exception:
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố, vui lòng thử lại sau.")

@router.post("/trich-xuat-van-ban")
async def extract_text(req: dict):
    try:
        file_url = req.get("file_url")
        if not file_url:
            raise HTTPException(status_code=400, detail="Thiếu file_url")
            
        from src.rag.ingestion_pipeline import ingestion_pipeline
        extracted_text = await ingestion_pipeline._extract_text(file_url)
        
        return {"extracted_text": extracted_text}
    except Exception as e:
        logger.error(f"Inference: Extraction failed: {e}")
        raise HTTPException(status_code=500, detail="Không thể trích xuất văn bản lúc này.")

@router.delete("/vector/{document_id}")
async def delete_vector_document(document_id: str):
    try:
        from src.store.vector_store import vector_store
        await vector_store.delete_by_document(document_id)
        return {"status": "success", "message": f"Deleted vectors for {document_id}"}
    except Exception as e:
        logger.error(f"Inference: Vector delete failed for {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
