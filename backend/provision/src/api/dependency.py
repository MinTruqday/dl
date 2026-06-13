from fastapi import Depends
from core.schemas.user import UserInDB
from core.dependency import (
    oauth2_scheme, get_db, get_current_user, get_current_user_optional,
    get_current_user_token_param, require_role, RateLimiter, require_permissions
)

async def check_quota(current_user: UserInDB = Depends(get_current_user)):
    from src.services.quota import QuotaService
    await QuotaService.check_quota(str(current_user.id), current_user.role.value)
    return current_user