from typing import Any, List, Optional

import httpx
from loguru import logger
from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, Query, Request, status
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
    request: Request,
    query: str = Query(min_length=1, max_length=1000),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user_optional),
    db=Depends(get_db),
):
    if not current_user:
        return APIResponse(
            data=await DocumentService.get_text_search(query, limit),
            message="Thực hiện truy vấn tìm kiếm văn bản hoàn tất",
        )

    rag_url = settings.AGENTIC_AI_URL
    if not rag_url:
        return APIResponse(
            data=await DocumentService.get_text_search(query, limit),
            message="Hệ thống AI tạm thời không khả dụng, đã tự động chuyển sang phương thức tìm kiếm tiêu chuẩn",
        )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{rag_url}/suy-luan/tim-kiem-tai-lieu",
                json={
                    "query": query,
                    "limit": min(limit, 30),
                },
                headers={
                    "Authorization": request.headers.get("Authorization", ""),
                },
            )
            if resp.status_code == 200:
                payload = resp.json()
                ranked = payload.get("results")
                if not isinstance(ranked, list):
                    raise ValueError("Semantic search response is invalid")
                documents = await DocumentService.get_ranked_public_documents(
                    ranked,
                    limit,
                )
                if documents:
                    return APIResponse(
                        data=documents,
                        message="Thực hiện truy vấn tìm kiếm ngữ nghĩa hoàn tất",
                    )
            logger.warning("Semantic search returned no ranked public documents")
            return APIResponse(
                data=await DocumentService.get_text_search(query, limit),
                message="Thực hiện truy vấn tìm kiếm văn bản hoàn tất",
            )
    except Exception:
        logger.exception("Semantic search execution error")
        return APIResponse(
            data=await DocumentService.get_text_search(query, limit),
            message="Hệ thống AI tạm thời không khả dụng, đã tự động chuyển sang phương thức tìm kiếm tiêu chuẩn",
        )

@router.get("/goi-y-ca-nhan", response_model=APIResponse[Any])
async def get_personalized_recommendations(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user_optional),
    db=Depends(get_db),
):
    if current_user:
        recommendations = await DocumentService.get_personalized_recommendations(
            str(current_user.id),
            limit,
        )
        if recommendations:
            return APIResponse(
                data=recommendations,
                message="Trích xuất danh sách khuyến nghị cá nhân hóa hoàn tất",
            )
    return APIResponse(
        data=await DocumentService.get_trending_documents(limit),
        message="Chưa đủ lịch sử đọc để cá nhân hóa nên hệ thống trả tài liệu thịnh hành",
    )
