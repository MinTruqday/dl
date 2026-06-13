from core.dependency import (RateLimiter, get_current_user,
                             get_current_user_optional,
                             get_current_user_token_param, get_db,
                             oauth2_scheme, require_permissions, require_role)
from core.schemas.user import UserInDB
from fastapi import Depends


async def check_quota(current_user: UserInDB = Depends(get_current_user)):
    from src.services.quota import QuotaService

    await QuotaService.check_quota(str(current_user.id), current_user.role.value)
    return current_user
