from typing import Any, List, Optional

from core.response import APIResponse
from core.schemas.user import UserInDB
from fastapi import APIRouter, Depends, Query, status
from src.api.dependency_router import get_current_user_optional, get_db
from src.services.document_service import DocumentService

router = APIRouter(prefix="/discovery")


@router.get("/xu-huong", response_model=APIResponse[Any])
async def get_trending_documents(limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), db=Depends(get_db)):
    return APIResponse(
        data=await DocumentService.get_trending_documents(limit),
        message="Đã tải danh sách tài liệu xu hướng",
        status=status.HTTP_200_OK,
    )


@router.get("/phan-loai", response_model=APIResponse[Any])
async def get_tags_categories(db=Depends(get_db)):
    return APIResponse(
        data=await DocumentService.get_tags_categories(),
        message="Đã tải danh sách thẻ và danh mục",
        status=status.HTTP_200_OK,
    )


@router.get("/tim-kiem-thong-minh", response_model=APIResponse[Any])
async def smart_search(
    query: str,
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    current_user: UserInDB = Depends(get_current_user_optional),
    db=Depends(get_db),
):
    if not current_user:
        return APIResponse(
            data=await DocumentService.get_text_search(query, limit),
            message="Tìm kiếm văn bản cơ bản",
        )

    import httpx
    from core.config import settings
    from fastapi import HTTPException
    from loguru import logger

    rag_url = settings.AGENTIC_AI_URL
    if not rag_url:
        return APIResponse(
            data=await DocumentService.get_text_search(query, limit),
            message="Hệ thống AI chưa được cấu hình, dùng tìm kiếm cơ bản",
        )

    try:
        async with httpx.AsyncClient(timeout=settings.LONG_PROCESS_TIMEOUT) as client:
            resp = await client.post(
                f"{rag_url}/chat",
                json={
                    "query": f"Tìm kiếm tài liệu liên quan đến: {query}",
                    "user_id": str(current_user.id),
                    "useSmart": True,
                },
            )
            if resp.status_code == 200:
                result = resp.json()
                return APIResponse(
                    data=result, message="Đã tìm kiếm thông minh bằng AI"
                )
            else:
                logger.error(
                    "Tìm kiếm thông minh thất bại với truy vấn '{query}': {resp.status_code}"
                )
                return APIResponse(
                    data=await DocumentService.get_text_search(query, limit),
                    message="Đã chuyển sang tìm kiếm tiêu chuẩn",
                )
    except Exception as e:
        logger.error("Tìm kiếm thông minh gặp ngoại lệ với truy vấn '{query}'")
        return APIResponse(
            data=await DocumentService.get_text_search(query, limit),
            message="Đã chuyển sang tìm kiếm tiêu chuẩn",
        )


@router.get("/suggestion/ai", response_model=APIResponse[Any])
async def get_ai_recommendations(
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    current_user: UserInDB = Depends(get_current_user_optional),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentService.get_trending_documents(limit),
        message="Đã tải gợi ý tài liệu từ AI",
    )


@router.get("/hashtag-xu-huong", response_model=APIResponse[Any])
async def get_trending_tags(limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), db=Depends(get_db)):
    return APIResponse(
        data=await DocumentService.get_trending_tags(limit),
        message="Đã tải danh sách hashtag xu hướng",
        status=status.HTTP_200_OK,
    )
