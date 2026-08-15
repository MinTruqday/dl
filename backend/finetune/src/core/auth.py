from enum import Enum
from typing import Any

import jwt
import redis.asyncio as redis
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.infrastructure.configuration import settings


class Role(str, Enum):
    READER = "reader"
    AUTHOR = "author"
    ADMIN = "admin"


class CurrentUser(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    id: str = Field(alias="_id")
    email: str
    role: Role = Role.READER
    permissions: list[str] = Field(default_factory=list)

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, value: Any):
        return value.lower() if isinstance(value, str) else value


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/xac-thuc/dang-nhap")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "authentication_required"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("uid")
        session_id = payload.get("sid")
        email = payload.get("sub")
        if not user_id or not session_id or not email:
            raise error
        client = redis.from_url(settings.REDIS_URI, decode_responses=True)
        try:
            valid = await client.sismember(f"user_sessions:{user_id}", session_id)
        finally:
            await client.aclose()
        if not valid:
            raise error
        return CurrentUser(
            _id=user_id,
            email=email,
            role=payload.get("role", "reader"),
            permissions=payload.get("permissions", []),
        )
    except (jwt.PyJWTError, ValueError):
        raise error


async def require_admin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "insufficient_permissions"},
        )
    return current_user
