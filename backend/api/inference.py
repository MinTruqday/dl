from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, HTTPException, Request, status
from .dependency import get_current_user
from models.user import UserInDB
import httpx
from core.config import settings

router = APIRouter(prefix="/inference")

RAG_SERVICE_URL = settings.AGENTIC_RAG_URL

async def proxy_post(path: str, payload: dict):
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(f"{RAG_SERVICE_URL}/inference/{path}", json=payload)
            if resp.status_code != 200:
                return APIResponse(data={"error": "Dịch vụ AI phản hồi lỗi, vui lòng thử lại sau."}, message="Dịch vụ AI gặp sự cố.", status=status.HTTP_502_BAD_GATEWAY)
            return APIResponse(data=resp.json(), message="Xử lý AI thành công.", status=status.HTTP_200_OK)
        except Exception as e:
            raise HTTPException(status_code=503, detail="Không thể kết nối đến máy chủ AI.")

@router.post("/generate-cover", response_model=APIResponse[Any])
async def generate_cover(payload: dict, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await proxy_post("generate-cover", payload), message="Yêu cầu tạo ảnh bìa thành công.", status=status.HTTP_200_OK)

@router.post("/analyze-sentiment", response_model=APIResponse[Any])
async def analyze_sentiment(payload: dict, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await proxy_post("analyze-sentiment", payload), message="Phân tích cảm xúc nội dung thành công.", status=200)

@router.post("/grammar-check", response_model=APIResponse[Any])
async def grammar_check(payload: dict, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await proxy_post("grammar-check", payload), message="Kiểm tra ngữ pháp thành công.", status=200)

@router.post("/synonyms", response_model=APIResponse[Any])
async def get_synonyms(payload: dict, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await proxy_post("synonyms", payload), message="Tìm từ đồng nghĩa thành công.", status=200)

@router.post("/translate", response_model=APIResponse[Any])
async def translate_text(payload: dict, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await proxy_post("translate", payload), message="Dịch thuật thành công.", status=status.HTTP_200_OK)

@router.post("/generate-code", response_model=APIResponse[Any])
async def generate_code(payload: dict, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await proxy_post("generate-code", payload), message="Tạo mã nguồn thành công.", status=status.HTTP_200_OK)
