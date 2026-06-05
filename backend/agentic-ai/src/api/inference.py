from fastapi import APIRouter, HTTPException
from typing import Optional, List, Any
from loguru import logger
from src.core.config import settings
from src.schemas.inference import (
    GenerationRequest, TranslationRequest, SentimentRequest,
    CoverRequest, CodeRequest, GrammarRequest, FlashcardRequest,
    SummarizeRequest, ActionRequest, MindmapRequest, CitationRequest,
    ToneRequest, ReviewRequest, SynthesisRequest
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
        prompt = f"OBJECTIVE: Translate the following text into {req.target_lang}. Output ONLY the translated text.\n\nTEXT:\n{req.text}"
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
            prompt = f"OBJECTIVE: Analyze the sentiment of the following text. Output ONLY one word: Positive, Negative, or Neutral.\n\nTEXT:\n{text}"
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
        
        summary_prompt = f"OBJECTIVE: Based on the following reviews, write a one-sentence summary of the overall reader sentiment.\nOUTPUT_LANGUAGE: Must match the language of the reviews.\n\nREVIEWS: {'; '.join(texts_to_analyze[:5])}"
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
        prompt = f"OBJECTIVE: Write clean and efficient {req.language} code for the following request. Output ONLY the code block.\n\nREQUEST:\n{req.prompt}"
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
        prompt = f"OBJECTIVE: Check and correct all spelling and grammar errors in the following text. Output ONLY the corrected text.\nOUTPUT_LANGUAGE: Must match the language of the input text.\n\nTEXT:\n{req.text}"
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
        prompt = f"OBJECTIVE: Create a high-quality flashcard with a front (question) and back (answer) based on the given text and context. Output ONLY valid JSON: {{'front': 'question', 'back': 'answer'}}.\nOUTPUT_LANGUAGE: Must match the language of the input text.\n\nCONTEXT: {req.context}\nTEXT: {req.text}"
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
        except Exception as err:
            logger.warning(f"Failed to parse JSON for flashcard: {err}")
        if ":" in result:
            parts = result.split(":", 1)
            return {"front": parts[0].strip(), "back": parts[1].strip()}
        return {"front": "Kiến thức quan trọng", "back": result.strip()}
    except Exception:
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố, vui lòng thử lại sau.")

@router.post("/tom-tat")
async def summarize_text(req: SummarizeRequest):
    try:
        prompt = f"OBJECTIVE: Provide a concise summary of the following content in {req.language}.\n\nTEXT:\n{req.text}"
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
        prompt = f"""SYSTEM IDENTITY: DocLib Core System - Plagiarism Detection Engine.
OBJECTIVE: Evaluate whether the similarity between the submitted text and matched sources indicates plagiarism.
OUTPUT_LANGUAGE: Must match the language of the submitted text.

SUBMITTED TEXT:
{req.text[:1000]}

MATCHED SOURCES:
{context}

INSTRUCTIONS:
1. Evaluate whether the similarity is coincidental or indicates copying.
2. Calculate a Plagiarism Score (0-100).
3. Output ONLY valid JSON: {{'plagiarism_score': float, 'status': 'clean|warning|danger', 'message': 'text', 'matched_sources': []}}
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
            "autocomplete": f"OBJECTIVE: Write one natural continuation sentence for the following text without repeating existing content. OUTPUT_LANGUAGE: Must match the input text language.\nCONTEXT: {req.context}\nTEXT: {req.text}",
            "grammar": f"OBJECTIVE: Fix all grammar and spelling errors. Output ONLY the corrected text. OUTPUT_LANGUAGE: Must match the input text language.\nTEXT: {req.text}",
            "summarize": f"OBJECTIVE: Provide a concise summary. OUTPUT_LANGUAGE: Must match the input text language.\nTEXT: {req.text}",
            "ai_suggestions": f"OBJECTIVE: Based on the context, suggest 3 development directions for this content. OUTPUT_LANGUAGE: Must match the input text language.\nCONTEXT: {req.context}\nTEXT: {req.text}",
            "check_logic": f"OBJECTIVE: Check for logical contradictions, plot holes, or character inconsistencies. OUTPUT_LANGUAGE: Must match the input text language.\nCONTEXT: {req.context}\nTEXT: {req.text}"
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
        prompt = f"OBJECTIVE: Find synonyms for the following word or phrase. Output ONLY a comma-separated list.\nOUTPUT_LANGUAGE: Must match the language of the input.\n\nINPUT: {req.text}"
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
        prompt = f"OBJECTIVE: Analyze the following text and generate a mindmap structure with depth {req.depth}. Output ONLY a single valid JSON object with no markdown or extra text. JSON structure: {{\"nodes\": [{{\"id\": \"root\", \"label\": \"node\"}}], \"edges\": [{{\"from\": \"root\", \"to\": \"node\"}}]}}.\nOUTPUT_LANGUAGE: Labels must match the language of the input text.\n\nTEXT: {req.text[:2000]}"
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
        except Exception as err:
            logger.warning(f"Failed to parse JSON for mindmap: {err}")
        return {"error": "Không thể tạo cấu trúc bản đồ tư duy"}
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
            
        prompt = f"OBJECTIVE: Based on the user's text and the reference sources found, suggest citations in {req.style} format.\nOUTPUT_LANGUAGE: Must match the language of the user's text.\n\nUSER TEXT: {req.text}\n\nREFERENCE SOURCES:\n" + "\n".join(sources)
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
        prompt = f"OBJECTIVE: {action.capitalize()} the following text to match the tone '{req.tone}'. Preserve core meaning while adjusting the linguistic style.\nOUTPUT_LANGUAGE: Must match the language of the input text.\n\nTEXT: {req.text}"
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
        prompt = f"SYSTEM IDENTITY: DocLib Core System - Content Review Engine.\nOBJECTIVE: Evaluate the following text based on these criteria: {criteria_str}. Provide a detailed report with Strengths, Weaknesses, and Improvement Suggestions.\nOUTPUT_LANGUAGE: Must match the language of the input text.\n\nTEXT: {req.text[:3000]}"
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
                
        prompt = f"OBJECTIVE: Synthesize information from multiple documents to answer the query: '{req.query}'.\nOUTPUT_LANGUAGE: Must match the language of the query.\n\nCONTEXT:\n" + "\n".join(all_context[:10])
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
