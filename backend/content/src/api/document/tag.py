from typing import Any, List
from fastapi import APIRouter, Query
from src.core.logging_route import LoggingRoute
from src.core.response import APIResponse
from src.services.document import DocumentService

router = APIRouter(route_class=LoggingRoute)

@router.get("/the-loai-va-nhan", response_model=APIResponse[Any])
async def get_tags_categories():
    return APIResponse(
        data=await DocumentService.get_tags_categories(),
        message="Truy xuất danh sách thể loại và nhãn thành công",
    )

@router.get("/nhan-thinh-hanh", response_model=APIResponse[List[str]])
async def get_trending_tags(limit: int = Query(default=20, le=100)):
    return APIResponse(
        data=await DocumentService.get_trending_tags(limit=limit),
        message="Truy xuất danh sách thẻ thịnh hành hoàn tất",
    )
