from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from src.core.response import APIResponse
from src.services.document import DocumentService

router = APIRouter()

@router.get("/tai-lieu", response_model=APIResponse[List[dict]])
async def search_documents_endpoint(
    q: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(default=20, ge=1, le=100),
):
    results = await DocumentService.search_documents(query=q, limit=limit)
    return APIResponse(data=results, message="Lấy danh sách tìm kiếm tài liệu thành công")
