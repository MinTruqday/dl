from typing import Any, Optional
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query, HTTPException
from models.user import UserInDB, RoleEnum
from api.dependency import get_db, require_role
from pydantic import BaseModel
import httpx
from core.config import settings

COLLECTOR_URL = "http://collector:8300"

class CollectionRequest(BaseModel):
    source: str
    pages: Optional[int] = 0

router = APIRouter(prefix='/thu-thap')

@router.post('/kich-hoat', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def trigger_collection(req: CollectionRequest, db=Depends(get_db)):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{COLLECTOR_URL}/thu-thap/kich-hoat", json={"source": req.source, "pages": req.pages})
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Lỗi thu thập"))
        return APIResponse(data=res.json(), message='Yêu cầu thu thập dữ liệu đã được gửi đi', status=202)

@router.post('/dung', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def stop_collection(db=Depends(get_db)):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{COLLECTOR_URL}/thu-thap/dung")
        return APIResponse(data=res.json(), message='Đã hủy bỏ toàn bộ quá trình thu thập', status=200)

@router.get('/thong-ke', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_collector_stats(db=Depends(get_db)):
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{COLLECTOR_URL}/thu-thap/thong-ke")
        return APIResponse(data=res.json(), message='Lấy số liệu thống kê thu thập thành công', status=200)

@router.get('/logs', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_collector_logs(db=Depends(get_db)):
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{COLLECTOR_URL}/thu-thap/logs")
        return APIResponse(data=res.json(), message='Lấy log thành công', status=200)