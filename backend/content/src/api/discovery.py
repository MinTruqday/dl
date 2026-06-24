from typing import Any, List, Optional

import httpx
from fastapi import APIRouter, Depends, Query, status
from src.api.dependency import get_current_user_optional, get_db
from src.services.document import DocumentService

from src.core.infrastructure.configuration import settings
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(prefix="/kham-pha")

@router.get("/thinh-hanh", response_model=APIResponse[Any])
async def get_trending_documents(
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentService.get_trending_documents(limit),
        message="Lấy danh sách tài liệu thịnh hành thành công",
        status=status.HTTP_200_OK,
    )

@router.get("/the-loai", response_model=APIResponse[Any])
async def get_tags_categories(db=Depends(get_db)):
    return APIResponse(
        data=await DocumentService.get_tags_categories(),
        message="Lấy danh sách thẻ và danh mục thành công",
        status=status.HTTP_200_OK,
    )

@router.get("/tim-kiem-thong-minh", response_model=APIResponse[Any])
async def smart_search(
    query: str,
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    current_user: CurrentUser = Depends(get_current_user_optional),
    db=Depends(get_db),
):
    if not current_user:
        return APIResponse(
            data=await DocumentService.get_text_search(query, limit),
            message="Thực hiện tìm kiếm văn bản thành công",
        )

    from src.core.infrastructure.configuration import settings as smart_settings

    rag_url = smart_settings.AGENTIC_AI_URL
    if not rag_url:
        return APIResponse(
            data=await DocumentService.get_text_search(query, limit),
            message="Lỗi tìm kiếm thông minh, đang dùng tìm kiếm tiêu chuẩn",
        )

    try:
        async with httpx.AsyncClient(timeout=smart_settings.LONG_PROCESS_TIMEOUT) as client:
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
    except Exception as e:
        logger.error(f"Lỗi tìm kiếm ngữ nghĩa: {e}")
        return APIResponse(
            data=await DocumentService.get_text_search(query, limit),
            message=f"Tìm kiếm tiêu chuẩn thành công: {e}",
        )

@router.get("/goi-y-ai", response_model=APIResponse[Any])
async def get_ai_recommendations(
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    current_user: CurrentUser = Depends(get_current_user_optional),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentService.get_trending_documents(limit),
        message="Lấy đề xuất tài liệu thành công",
    )

@router.get("/tu-khoa-thinh-hanh", response_model=APIResponse[Any])
async def get_trending_tags(
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentService.get_trending_tags(limit),
        message="Lấy danh sách hashtag thịnh hành thành công",
        status=status.HTTP_200_OK,
    )
