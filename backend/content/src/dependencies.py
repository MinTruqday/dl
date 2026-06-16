import httpx
from core.config import settings
from core.dependency import get_current_user
from fastapi import Depends, HTTPException
from loguru import logger

async def check_quota(current_user: dict = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient(timeout=settings.DEFAULT_HTTP_TIMEOUT) as client:
            resp = await client.get(
                f"{settings.MANAGEMENT_URL}/han-muc/xac-minh",
                params={"user_id": str(current_user.get("id")), "role": current_user.get("role").value},
            )
            if resp.status_code == 429:
                raise HTTPException(status_code=429, detail="Lỗi truy xuất cơ sở dữ liệu hệ thống")
            elif resp.status_code != 200:
                logger.warning("Lỗi truy xuất cơ sở dữ liệu hệ thống")
    except HTTPException:
        raise
    except Exception:
        logger.error("Mất kết nối mạng tạm thời")
    return current_user