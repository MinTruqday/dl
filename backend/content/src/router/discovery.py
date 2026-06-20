from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query, status
from src.router.dependency import get_current_user_optional, get_db
from src.services.document import DocumentService

from core.config import settings
from core.response import APIResponse
from core.schemas.user import UserInDB

router = APIRouter(prefix="/discovery")


@router.get("/trending", response_model=APIResponse[Any])
async def get_trending_documents(
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentService.get_trending_documents(limit),
        message="Lấy danh sách tài liệu thịnh hành thành công",
        status=status.HTTP_200_OK,
    )


@router.get("/genres", response_model=APIResponse[Any])
async def get_tags_categories(db=Depends(get_db)):
    return APIResponse(
        data=await DocumentService.get_tags_categories(),
        message="Lấy danh sách thẻ và danh mục thành công",
        status=status.HTTP_200_OK,
    )


@router.get("/smart-search", response_model=APIResponse[Any])
async def smart_search(
    query: str,
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    current_user: UserInDB = Depends(get_current_user_optional),
    db=Depends(get_db),
):
    if not current_user:
        return APIResponse(
            data=await DocumentService.get_text_search(query, limit),
            message="Thực hiện tìm kiếm văn bản thành công",
        )

    import httpx
    from loguru import logger

    from core.config import settings

    rag_url = settings.AGENTIC_AI_URL
    if not rag_url:
        return APIResponse(
            data=await DocumentService.get_text_search(query, limit),
            message="Lỗi tìm kiếm thông minh, đang dùng tìm kiếm tiêu chuẩn",
        )

    try:
        async with httpx.AsyncClient(timeout=settings.LONG_PROCESS_TIMEOUT) as client:
            resp = await client.post(
                f"{rag_url}/chat",
                json={
                    "query": f"Searching for documents related to the requested criteria",
                    "user_id": str(current_user.id),
                    "useSmart": True,
                },
            )
            if resp.status_code == 200:
                result = resp.json()
                return APIResponse(data=result, message="Tìm kiếm ngữ nghĩa thành công")
            else:
                logger.error("Lỗi tìm kiếm thông minh")
                return APIResponse(
                    data=await DocumentService.get_text_search(query, limit),
                    message="Tìm kiếm tiêu chuẩn thành công",
                )
    except Exception:
        logger.error("Lỗi tìm kiếm ngữ nghĩa")
        return APIResponse(
            data=await DocumentService.get_text_search(query, limit),
            message="Tìm kiếm tiêu chuẩn thành công",
        )


@router.get("/ai-suggestions", response_model=APIResponse[Any])
async def get_ai_recommendations(
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    current_user: UserInDB = Depends(get_current_user_optional),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentService.get_trending_documents(limit),
        message="Lấy đề xuất tài liệu thành công",
    )


@router.get("/trending-hashtags", response_model=APIResponse[Any])
async def get_trending_tags(
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentService.get_trending_tags(limit),
        message="Lấy danh sách hashtag thịnh hành thành công",
        status=status.HTTP_200_OK,
    )
