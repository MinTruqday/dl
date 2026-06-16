import httpx
from core.config import settings
from core.dependency import get_current_user
from fastapi import Depends, HTTPException
from loguru import logger

async def check_quota(current_user: dict = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient(timeout=settings.DEFAULT_HTTP_TIMEOUT) as client:
            resp = await client.get(
                f"{settings.PROVISION_URL}/quota/verify",
                params={"user_id": str(current_user.get("id")), "role": current_user.get("role").value},
            )
            if resp.status_code == 429:
                raise HTTPException(status_code=429, detail="Storage quota exceeded allocated operational limits")
            elif resp.status_code != 200:
                logger.warning("System failed to securely verify storage quota attributes from provisioning subsystem")
    except HTTPException:
        raise
    except Exception:
        logger.error("Internal service network failure occurred attempting connection with remote provisioning subsystem")
    return current_user