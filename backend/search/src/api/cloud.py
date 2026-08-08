from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from src.core.logging_route import LoggingRoute
from src.core.response import APIResponse
from src.api.dependency import get_current_user, CurrentUser
from src.services.cloud import CloudService

router = APIRouter(route_class=LoggingRoute)

@router.get("/luu-tru", response_model=APIResponse[List[dict]])
async def search_cloud_items_endpoint(
    q: Optional[str] = Query(default=None, max_length=200),
    mime_type: Optional[str] = Query(default=None, max_length=100),
    extension: Optional[str] = Query(default=None, max_length=10),
    min_size_mb: Optional[float] = Query(default=None, ge=0),
    max_size_mb: Optional[float] = Query(default=None, ge=0),
    current_user: CurrentUser = Depends(get_current_user),
):
    results = await CloudService.advanced_search(
        owner_id=str(current_user.id),
        query_text=q,
        mime_type=mime_type,
        extension=extension,
        min_size_mb=min_size_mb,
        max_size_mb=max_size_mb,
    )
    return APIResponse(data=results, message="Lấy danh sách tìm kiếm lưu trữ thành công")
