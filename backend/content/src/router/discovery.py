import httpx
from core.config import settings
from typing import Any, Optional
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query, status
from core.dependency import get_current_user_optional, get_db
from src.services.documents import DocumentService
from loguru import logger

router = APIRouter(prefix="/kham-pha")

@router.get("/thinh-hanh", response_model=APIResponse[Any])
async def get_trending_documents(limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), db=Depends(get_db)):
    return APIResponse(
        data=await DocumentService.get_trending_documents(limit),
        message="Lỗi khi truy xuất tài liệu",
        status=status.HTTP_200_OK,
    )

@router.get("/the-loai", response_model=APIResponse[Any])
async def get_tags_categories(db=Depends(get_db)):
    return APIResponse(
        data=await DocumentService.get_tags_categories(),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
        status=status.HTTP_200_OK,
    )

@router.get("/thong-minh-tim-kiem", response_model=APIResponse[Any])
async def smart_search(query: str, limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), current_user: dict = Depends(get_current_user_optional), db=Depends(get_db)):
    if not current_user:
        return APIResponse(
            data=await DocumentService.get_text_search(query, limit),
            message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
        )

    rag_url = settings.AGENTIC_AI_URL
    if not rag_url:
        return APIResponse(
            data=await DocumentService.get_text_search(query, limit),
            message="Lỗi khi truy xuất tài liệu",
        )

    try:
        async with httpx.AsyncClient(timeout=settings.LONG_PROCESS_TIMEOUT) as client:
            resp = await client.post(
                f"{rag_url}/tro-chuyen",
                json={"query": "Searching for documents related to requested criteria", "user_id": str(current_user.get("id")), "useSmart": True},
            )
            if resp.status_code == 200:
                return APIResponse(data=resp.json(), message="Khởi tạo danh mục tìm kiếm thành công")
            else:
                logger.error("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
                return APIResponse(data=await DocumentService.get_text_search(query, limit), message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
    except Exception:
        logger.error("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        return APIResponse(data=await DocumentService.get_text_search(query, limit), message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")

@router.get("/ai-goi-y", response_model=APIResponse[Any])
async def get_ai_recommendations(limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), current_user: dict = Depends(get_current_user_optional), db=Depends(get_db)):
    return APIResponse(
        data=await DocumentService.get_trending_documents(limit),
        message="Lỗi truy xuất cơ sở dữ liệu hệ thống",
    )

@router.get("/thinh-hanh-nhan-dan", response_model=APIResponse[Any])
async def get_trending_tags(limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), db=Depends(get_db)):
    return APIResponse(
        data=await DocumentService.get_trending_tags(limit),
        message="Lỗi truy xuất cơ sở dữ liệu hệ thống",
        status=status.HTTP_200_OK,
    )