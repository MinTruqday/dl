from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, HTTPException, Request, status
from .dependency import get_current_user, check_quota
from models.user import UserInDB
import httpx
from core.config import settings

router = APIRouter(prefix="/suy-luan")

RAG_SERVICE_URL = settings.AGENTIC_AI_URL

async def proxy_post(path: str, payload: dict):
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(f"{RAG_SERVICE_URL}/inference/{path}", json=payload)
            if resp.status_code != 200:
                return APIResponse(data={"error": "Dịch vụ AI phản hồi lỗi, vui lòng thử lại sau"}, message="Dịch vụ AI gặp sự cố", status=status.HTTP_502_BAD_GATEWAY)
            return APIResponse(data=resp.json(), message="Xử lý AI thành công", status=status.HTTP_200_OK)
        except Exception as e:
            raise HTTPException(status_code=503, detail="Không thể kết nối đến máy chủ AI")

@router.post("/tao-anh-bia", response_model=APIResponse[Any])
async def generate_cover(payload: dict, current_user: UserInDB = Depends(check_quota)):
    document_id = payload.get("document_id")
    if document_id:
        from services.editor import EditorService
        style = payload.get("style", "minimalist")
        return APIResponse(data=await EditorService.generate_cover(document_id, style, current_user), message="Yêu cầu tạo ảnh bìa thành công", status=status.HTTP_200_OK)
    return APIResponse(data=await proxy_post("tao-anh-bia", payload), message="Yêu cầu tạo ảnh bìa thành công", status=status.HTTP_200_OK)

@router.post("/phan-tich-cam-xuc", response_model=APIResponse[Any])
async def analyze_sentiment(payload: dict, current_user: UserInDB = Depends(check_quota)):
    return APIResponse(data=await proxy_post("phan-tich-cam-xuc", payload), message="Phân tích cảm xúc nội dung thành công", status=200)

@router.post("/kiem-tra-ngu-phap", response_model=APIResponse[Any])
async def grammar_check(payload: dict, current_user: UserInDB = Depends(check_quota)):
    return APIResponse(data=await proxy_post("kiem-tra-ngu-phap", payload), message="Kiểm tra ngữ pháp thành công", status=200)

@router.post("/tu-dong-nghia", response_model=APIResponse[Any])
async def get_synonyms(payload: dict, current_user: UserInDB = Depends(check_quota)):
    return APIResponse(data=await proxy_post("tu-dong-nghia", payload), message="Tìm từ đồng nghĩa thành công", status=200)

@router.post("/dich-thuat", response_model=APIResponse[Any])
async def translate_text(payload: dict, current_user: UserInDB = Depends(check_quota)):
    return APIResponse(data=await proxy_post("dich-thuat", payload), message="Dịch thuật thành công", status=status.HTTP_200_OK)

@router.post("/tao-ma-nguon", response_model=APIResponse[Any])
async def generate_code(payload: dict, current_user: UserInDB = Depends(check_quota)):
    return APIResponse(data=await proxy_post("tao-ma-nguon", payload), message="Tạo mã nguồn thành công", status=status.HTTP_200_OK)
