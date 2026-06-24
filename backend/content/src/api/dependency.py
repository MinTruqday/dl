import httpx
from fastapi import Depends, HTTPException
from loguru import logger

from shared.infrastructure.configuration import settings
from shared.dependency import (
    RateLimiting,
    get_current_user,
    get_current_user_optional,
    get_current_user_token_param,
    get_db,
    oauth2_scheme,
    require_permissions,
    require_role,
)
from shared.dependency import CurrentUser, Role


async def check_quota(current_user: CurrentUser = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient(timeout=settings.DEFAULT_HTTP_TIMEOUT) as client:
            resp = await client.get(
                f"{settings.MANAGEMENT_URL}/han-muc/xac-minh",
                params={
                    "user_id": str(current_user.id),
                    "role": current_user.role.value,
                },
            )
            if resp.status_code == 429:
                raise HTTPException(
                    status_code=429,
                    detail=resp.json().get("detail", "StorageService quota exceeded"),
                )
            elif resp.status_code != 200:
                logger.warning("Lỗi xác minh dung lượng lưu trữ")
    except Exception as e:
        logger.error("Lỗi kết nối nền")
    return current_user
