from typing import Any, Optional
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query
from models.user import UserInDB, RoleEnum
from api.dependency import require_role
from services.collector import CollectorService
from pydantic import BaseModel

router = APIRouter(prefix="/thu-thap")

class CollectionRequest(BaseModel):
    source: str
    url: Optional[str] = None
    index_type: Optional[str] = "list"
    target_class: Optional[str] = None

@router.post("/kich-hoat", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def trigger_collection(req: CollectionRequest):
    return APIResponse(
        data=await CollectorService.trigger_collection(req.source, req.url, req.index_type, req.target_class),
        message="Yêu cầu thu thập dữ liệu đã được gửi đi",
        status=202
    )

@router.get("/thong-ke", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def get_collector_stats():
    return APIResponse(
        data=await CollectorService.get_collector_stats(),
        message="Lấy số liệu thống kê thu thập thành công",
        status=200
    )
