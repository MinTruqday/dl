import httpx
from core.config import settings
from core.dependency import (
    RateLimiter,
    get_current_user,
    get_current_user_optional,
    get_current_user_token_param,
    get_db,
    oauth2_scheme,
    require_permissions,
    require_role,
)
from core.schemas.user import UserInDB
from fastapi import Depends, HTTPException
from loguru import logger


async def check_quota(current_user: UserInDB = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient(timeout=settings.DEFAULT_HTTP_TIMEOUT) as client:
            resp = await client.get(
                f"{settings.PROVISION_URL}/quota/check",
                params={
                    "user_id": str(current_user.id),
                    "role": current_user.role.value,
                },
            )
            if resp.status_code == 429:
                raise HTTPException(
                    status_code=429,
                    detail=resp.json().get("detail", "Vượt quá hạn mức"),
                )
            elif resp.status_code != 200:
                logger.warning(
                    f"Không thể kiểm tra hạn mức từ hệ thống vận hành: {resp.status_code}"
                )
    except Exception as e:
        logger.error("Lỗi kết nối tới hệ thống vận hành")
    return current_user
