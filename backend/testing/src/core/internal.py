import hmac

from fastapi import Header, HTTPException

from src.core.configuration import settings


async def require_internal_token(x_internal_token: str = Header(default="")):
    if not hmac.compare_digest(x_internal_token, settings.SECRET_KEY):
        raise HTTPException(status_code=403, detail={"code": "INVALID_INTERNAL_TOKEN"})
