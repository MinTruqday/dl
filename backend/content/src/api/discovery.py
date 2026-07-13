from typing import Any, List, Optional

import httpx
from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, Query, status
from src.api.dependency import get_current_user_optional, get_db
from src.services.document import DocumentService

from src.core.infrastructure.configuration import settings
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(route_class=LoggingRoute, prefix="/kham-pha")

@router.get("/the-loai", response_model=APIResponse[Any])
async def get_tags_categories(db=Depends(get_db)):
    return APIResponse(
        data=await DocumentService.get_tags_categories(),
        message="Trích xuất danh sách thẻ và danh mục hệ thống hoàn tất",
        status=status.HTTP_200_OK,
    )

@router.get("/tim-kiem-thong-minh", response_model=APIResponse[Any])
async def smart_search(
    query: str,
    limit: int = Query(default=20, le=100),
    current_user: CurrentUser = Depends(get_current_user_optional),
    db=Depends(get_db),
):
    if not current_user:
        return APIResponse(
            data=await DocumentService.get_text_search(query, limit),
            message="Thực hiện truy vấn tìm kiếm văn bản hoàn tất",
        )

    from src.core.infrastructure.configuration import settings as smart_settings

    rag_url = smart_settings.AGENTIC_AI_URL
    if not rag_url:
        return APIResponse(
            data=await DocumentService.get_text_search(query, limit),
            message="Hệ thống AI tạm thời không khả dụng, đã tự động chuyển sang phương thức tìm kiếm tiêu chuẩn",
        )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{rag_url}/chat",
                json={
                    "query": f"Searching for documents related to the requested criteria",
                    "user_id": str(current_user.id),
                    "thinking": True,
                },
            )
            if resp.status_code == 200:
                result = resp.json()
                return APIResponse(data=result, message="Thực hiện truy vấn tìm kiếm ngữ nghĩa hoàn tất")
            else:
                logger.error("Smart search query failed")
                return APIResponse(
                    data=await DocumentService.get_text_search(query, limit),
                    message="Thực hiện truy vấn tìm kiếm văn bản hoàn tất",
                )
    except Exception as e:
        logger.exception("Semantic search execution error")
        return APIResponse(
            data=await DocumentService.get_text_search(query, limit),
            message="Hệ thống AI tạm thời không khả dụng, đã tự động chuyển sang phương thức tìm kiếm tiêu chuẩn",
        )

@router.get("/goi-y-ai", response_model=APIResponse[Any])
async def get_ai_recommendations(
    limit: int = Query(default=20, le=100),
    current_user: CurrentUser = Depends(get_current_user_optional),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentService.get_trending_documents(limit),
        message="Trích xuất danh sách đề xuất tài liệu từ hệ thống AI hoàn tất",
    )


