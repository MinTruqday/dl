from fastapi import Depends, HTTPException
from core.schemas.user import UserInDB
from core.dependency import (
    oauth2_scheme, get_db, get_current_user, get_current_user_optional,
    get_current_user_token_param, require_role, RateLimiter, require_permissions
)
import httpx
from core.config import settings
from loguru import logger

async def check_quota(current_user: UserInDB = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(
                f"{settings.PROVISION_URL}/quota/kiem-tra",
                params={"user_id": str(current_user.id), "role": current_user.role.value}
            )
            if resp.status_code == 429:
                raise HTTPException(status_code=429, detail=resp.json().get('detail', 'Vượt quá hạn mức'))
            elif resp.status_code != 200:
                logger.warning(f"Không thể kiểm tra hạn mức từ hệ thống vận hành: {resp.status_code}")
    except Exception as e:
        logger.error("Lỗi kết nối tới hệ thống vận hành")
    return current_user