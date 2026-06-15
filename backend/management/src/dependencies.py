from core.dependency import get_current_user
from core.schemas.user import UserInDB
from fastapi import Depends
from src.services.quotas import QuotaService

async def check_quota(current_user: UserInDB = Depends(get_current_user)):
    await QuotaService.check_quota(str(current_user.id), current_user.role.value)
    return current_user