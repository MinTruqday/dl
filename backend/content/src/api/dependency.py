import httpx
from fastapi import Depends, HTTPException
from loguru import logger

from src.core.infrastructure.configuration import settings
from src.core.dependency import (
    RateLimiting,
    get_current_user,
    get_current_user_optional,
    get_current_user_token_param,
    get_db,
    oauth2_scheme,
    require_permissions,
    require_role,
)
from src.core.dependency import CurrentUser, Role

async def check_quota(current_user: CurrentUser = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.USAGE_URL}/han-muc/xac-minh",
                params={
                    "user_id": str(current_user.id),
                    "role": current_user.role.value,
                },
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
            if resp.status_code == 429:
                raise HTTPException(
                    status_code=429,
                    detail=resp.json().get("detail", "StorageService quota exceeded"),
                )
            elif resp.status_code != 200:
                logger.warning("Storage quota verification failed")
    except Exception as e:
        logger.exception("Background service connection error")
    return current_user
