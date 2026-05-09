from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Any
from loguru import logger
from src.core.config import settings
from huggingface_hub import AsyncInferenceClient
import httpx
import base64
import asyncio

router = APIRouter()

class GenerationRequest(BaseModel):
    prompt: str
    max_tokens: int = 500
    temperature: float = 0.3

class TranslationRequest(BaseModel):
    text: str
    target_lang: str

class SentimentRequest(BaseModel):
    texts: List[str]

class CoverRequest(BaseModel):
    title: str
    description: str = ""
    style: str = "photorealistic"

class CodeRequest(BaseModel):
    prompt: str
    language: str = "python"

class GrammarRequest(BaseModel):
    text: str

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

@router.post("/generate")
async def generate_text(req: GenerationRequest):
    try:
        result = await _chat_direct(
            messages=[{"role": "user", "content": req.prompt}],
            max_tokens=req.max_tokens,
            temperature=req.temperature
        )
        return {"result": result}
    except Exception:
        raise HTTPException(status_code=500, detail="Lỗi khi tạo văn bản bằng trí tuệ nhân tạo")

@router.post("/translate")
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
        raise HTTPException(status_code=500, detail="Lỗi khi dịch thuật văn bản")

@router.post("/analyze-sentiment")
async def analyze_sentiment(req: SentimentRequest):
    try:
        results = []
        for text in req.texts:
            prompt = f"Phân tích cảm xúc của đoạn văn sau. Trả lời duy nhất 1 từ (Tích cực, Tiêu cực hoặc Trung lập):\n\n{text}"
            sentiment = await _chat_direct(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.1
            )
            results.append({"text": text, "sentiment": sentiment.strip()})
        return {"analysis": results}
    except Exception:
        raise HTTPException(status_code=500, detail="Lỗi khi phân tích cảm xúc")

@router.post("/generate-cover")
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
        raise HTTPException(status_code=500, detail="Lỗi hệ thống khi tạo ảnh bìa")

@router.post("/generate-code")
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
        raise HTTPException(status_code=500, detail="Lỗi khi tạo mã nguồn bằng AI")

@router.post("/grammar-check")
async def grammar_check(req: GrammarRequest):
    try:
        prompt = f"Kiểm tra và sửa lỗi chính tả, ngữ pháp cho đoạn văn bản sau. Chỉ trả về đoạn văn đã sửa:\n\n{req.text}"
        result = await _chat_direct(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=len(req.text) + 200,
            temperature=0.1
        )
        return {"corrected_text": result.strip()}
    except Exception:
        raise HTTPException(status_code=500, detail="Lỗi khi kiểm tra ngữ pháp")

@router.post("/synonyms")
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
        raise HTTPException(status_code=500, detail="Lỗi khi tìm từ đồng nghĩa")
