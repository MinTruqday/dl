from fastapi import APIRouter, Depends, HTTPException
from typing import Any
from src.core.logging_route import LoggingRoute
from src.core.response import APIResponse
from src.schemas.tier import UpdateTierRequest, UsageTierResponse
from src.services.tier import TierService
from src.core.dependency import get_db, verify_internal_token

router = APIRouter(route_class=LoggingRoute, prefix="/goi-cuoc")

@router.get("/{user_id}", response_model=APIResponse[UsageTierResponse], dependencies=[Depends(verify_internal_token)])
async def get_user_tier(user_id: str, db=Depends(get_db)):
    tier_info = await TierService.get_user_tier(user_id)
    return APIResponse(data=tier_info, message="Trích xuất thông tin gói cước tài khoản hoàn tất")

@router.put("/{user_id}", response_model=APIResponse[UsageTierResponse], dependencies=[Depends(verify_internal_token)])
async def update_user_tier(user_id: str, req: UpdateTierRequest, db=Depends(get_db)):
    updated_tier = await TierService.update_user_tier(user_id, req)
    return APIResponse(data=updated_tier, message="Cập nhật cấu hình gói cước tài khoản hoàn tất")
