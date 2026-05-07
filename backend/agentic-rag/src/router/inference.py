from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Any
from loguru import logger
from langchain_huggingface import HuggingFaceEndpoint
from src.core.config import settings
import httpx
import base64

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

def get_llm(temperature: float = 0.3):
    return HuggingFaceEndpoint(
        repo_id=settings.LLAMA_MODEL,
        huggingfacehub_api_token=settings.HF_TOKEN,
        temperature=temperature,
        max_new_tokens=1024
    )

@router.post("/generate")
async def generate_text(req: GenerationRequest):
    try:
        llm = get_llm(req.temperature)
        result = await llm.ainvoke(req.prompt)
        return {"result": result}
    except Exception as e:
logger.info("Log message sanitized"))
        raise HTTPException(status_code=500, detail="Lỗi khi tạo văn bản bằng AI.")

@router.post("/translate")
async def translate_text(req: TranslationRequest):
    try:
        llm = get_llm(0.1)
        prompt = f"Dịch đoạn văn bản sau sang {req.target_lang}. Chỉ trả về bản dịch:\n\n{req.text}"
        result = await llm.ainvoke(prompt)
        return {"translation": result.strip()}
    except Exception as e:
logger.info("Log message sanitized"))
        raise HTTPException(status_code=500, detail="Lỗi khi dịch thuật văn bản.")

@router.post("/analyze-sentiment")
async def analyze_sentiment(req: SentimentRequest):
    try:
        llm = get_llm(0.1)
        results = []
        for text in req.texts:
            prompt = f"Phân tích cảm xúc của đoạn văn sau (Tích cực/Tiêu cực/Trung lập). Trả lời duy nhất 1 từ:\n\n{text}"
            res = await llm.ainvoke(prompt)
            results.append({"text": text, "sentiment": res.strip()})
        return {"analysis": results}
    except Exception as e:
logger.info("Log message sanitized"))
        raise HTTPException(status_code=500, detail="Lỗi khi phân tích cảm xúc.")

@router.post("/generate-cover")
async def generate_cover(req: CoverRequest):
    try:
        image_gen_model = settings.IMAGE_GEN_MODEL
        if not image_gen_model:
            raise HTTPException(status_code=503, detail="Mô hình tạo ảnh chưa được cấu hình.")
            
        prompt = f"Book cover for '{req.title}'. Description: {req.description}. Style: {req.style}. High quality, cinematic."
        
        headers = {"Authorization": f"Bearer {settings.HF_TOKEN}"}
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"https://api-inference.huggingface.co/models/{image_gen_model}",
                headers=headers,
                json={"inputs": prompt}
            )
            if resp.status_code == 200:
                image_bytes = resp.content
                base64_image = base64.b64encode(image_bytes).decode("utf-8")
                return {"cover_url": f"data:image/jpeg;base64,{base64_image}", "message": "Đã tạo ảnh bìa bằng mô hình FLUX thành công."}
            else:
logger.info("Log message sanitized"))
                return {"cover_url": "https://placehold.co/600x400?text=Error+Generating+Cover", "message": "Gặp sự cố khi gọi mô hình FLUX."}
    except Exception as e:
logger.info("Log message sanitized"))
        raise HTTPException(status_code=500, detail="Lỗi hệ thống khi tạo ảnh bìa.")

@router.post("/generate-code")
async def generate_code(req: CodeRequest):
    try:
        llm = get_llm(0.2)
        prompt = f"Write clean, efficient {req.language} code for the following requirement. Only return the code block:\n\n{req.prompt}"
        result = await llm.ainvoke(prompt)
        return {"code": result.strip()}
    except Exception as e:
logger.info("Log message sanitized"))
        raise HTTPException(status_code=500, detail="Lỗi khi tạo mã nguồn bằng AI.")

@router.post("/grammar-check")
async def grammar_check(req: GrammarRequest):
    try:
        llm = get_llm(0.1)
        prompt = f"Kiểm tra và sửa lỗi chính tả, ngữ pháp cho đoạn văn bản sau. Chỉ trả về đoạn văn đã sửa:\n\n{req.text}"
        result = await llm.ainvoke(prompt)
        return {"corrected_text": result.strip()}
    except Exception as e:
logger.info("Log message sanitized"))
        raise HTTPException(status_code=500, detail="Lỗi khi kiểm tra ngữ pháp.")

@router.post("/synonyms")
async def get_synonyms(req: GrammarRequest):
    try:
        llm = get_llm(0.5)
        prompt = f"Tìm các từ đồng nghĩa cho cụm từ hoặc đoạn văn sau. Chỉ trả về danh sách phân cách bằng dấu phẩy:\n\n{req.text}"
        result = await llm.ainvoke(prompt)
        return {"synonyms": result.strip().split(", ")}
    except Exception as e:
logger.info("Log message sanitized"))
        raise HTTPException(status_code=500, detail="Lỗi khi tìm từ đồng nghĩa.")
