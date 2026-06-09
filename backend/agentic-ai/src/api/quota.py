from typing import Any
from fastapi import APIRouter, Depends
from src.core.config import settings
from src.core.response import APIResponse
from src.schemas.quota import QuotaLimit
from src.services.quota import QuotaService

router = APIRouter(prefix='/quota')

async def get_db():
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    return client[settings.MONGODB_DB_NAME]

async def get_current_user_id(request: Any = None):
    from fastapi import Request, Header, HTTPException
    return None

@router.get('/me', response_model=APIResponse[Any])
async def get_my_quota(
    x_user_id: str = Depends(lambda: None),
    x_user_role: str = Depends(lambda: None),
):
    from fastapi import Header, HTTPException
    return APIResponse(data={}, message='Endpoint này cần x_user_id header')

@router.get('/su-dung/{user_id}', response_model=APIResponse[Any])
async def get_user_quota_usage(user_id: str, role: str = 'reader'):
    db = await get_db()
    usage = await QuotaService.get_current_usage(user_id, role, db=db)
    return APIResponse(data=usage, message='Lấy thông tin hạn mức thành công')

@router.put('/config/{role}', response_model=APIResponse[Any])
async def update_role_quota(role: str, limits: QuotaLimit):
    db = await get_db()
    result = await QuotaService.update_global_limits(role, limits, db=db)
    return APIResponse(data=result, message='Cập nhật cấu hình hạn mức thành công')

@router.get('/config', response_model=APIResponse[Any])
async def get_global_config():
    db = await get_db()
    config = await QuotaService._get_global_config(db=db)
    return APIResponse(data=config.role_limits, message='Lấy cấu hình hạn mức thành công')