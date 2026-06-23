from shared.dependencies import CurrentUser
from fastapi import Depends

from shared.dependencies import (
    RateLimiting,
    get_current_user,
    get_current_user_optional,
    get_current_user_token_param,
    get_db,
    oauth2_scheme,
    require_permissions,
    require_role,
)
from src.schemas.profiles import UserInDB


async def check_quota(current_user: CurrentUser = Depends(get_current_user)):
    from src.services.usage_quotas import UsageQuota

    await UsageQuota.check_quota(str(current_user.id), current_user.role.value)
    return current_user
