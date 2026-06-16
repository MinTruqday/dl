from core.dependency import get_current_user
from fastapi import Depends
from src.services.quotas import QuotaService

async def check_quota(current_user: dict = Depends(get_current_user)):
    await QuotaService.check_quota(str(current_user.get("id")), current_user.get("role").value)
    return current_user