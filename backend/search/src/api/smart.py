from typing import List, Optional
from fastapi import APIRouter, Header, Query
from src.core.response import APIResponse
from src.services.smart import SmartService

router = APIRouter()

@router.get("/thong-minh", response_model=APIResponse[List[dict]])
async def smart_search_endpoint(
    q: str = Query(..., min_length=1, max_length=1000),
    limit: int = Query(default=20, ge=1, le=100),
    authorization: Optional[str] = Header(default=None),
):
    results = await SmartService.smart_search(
        query=q,
        limit=limit,
        authorization_header=authorization,
    )
    return APIResponse(data=results, message="Tìm kiếm thông minh thành công")
