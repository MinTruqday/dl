import hmac
from enum import Enum
from typing import Any, List, Optional

import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.redis import redis


class Role(str, Enum):
    GUEST = "guest"
    READER = "reader"
    AUTHOR = "author"
    ADMIN = "admin"


class CurrentUser(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str = Field(alias="_id")
    email: str
    role: Role = Role.READER
    permissions: List[str] = Field(default_factory=list)
    is_active: bool = True
    full_name: str = ""
    slug: str = ""

    @field_validator("role", mode="before")
    @classmethod
    def validate_role_case(cls, value: Any):
        return value.lower() if isinstance(value, str) else value


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/xac-thuc/dang-nhap")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại hệ thống",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        session_id = payload.get("sid")
        user_id = payload.get("uid")
        if not email or not session_id or not user_id:
            raise exception
    except jwt.PyJWTError:
        raise exception
    if not await redis.sismember(f"user_sessions:{user_id}", session_id):
        raise exception
    return CurrentUser(
        _id=user_id,
        email=email,
        role=payload.get("role", "reader"),
        permissions=payload.get("permissions", []),
        full_name=payload.get("full_name", ""),
        slug=payload.get("slug", ""),
    )


async def get_current_user_optional(
    token: Optional[str] = Depends(
        OAuth2PasswordBearer(tokenUrl="/xac-thuc/dang-nhap", auto_error=False)
    ),
) -> Optional[CurrentUser]:
    if not token:
        return None
    try:
        return await get_current_user(token)
    except HTTPException:
        return None


def require_role(required_roles: List[Role]):
    async def role_checker(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if current_user.role == Role.ADMIN or current_user.role in required_roles:
            return current_user
        raise HTTPException(status_code=403, detail="Bạn không có quyền thực hiện thao tác này")

    return role_checker


def require_permissions(required_permissions: List[str]):
    async def permission_checker(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if current_user.role == Role.ADMIN:
            return current_user
        if any(item not in current_user.permissions for item in required_permissions):
            raise HTTPException(status_code=403, detail="Tài khoản không có đủ quyền hạn")
        return current_user

    return permission_checker


async def verify_internal_token(x_internal_token: str = Header(default="")):
    if not settings.SECRET_KEY or not hmac.compare_digest(
        x_internal_token.encode("utf-8"), settings.SECRET_KEY.encode("utf-8")
    ):
        raise HTTPException(status_code=403, detail="Mã xác thực nội bộ không hợp lệ")


class RateLimiting:
    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period

    async def __call__(self, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}:{request.url.path}"
        current = await redis.get(key)
        if current is not None and int(current) >= self.calls:
            raise HTTPException(status_code=429, detail="Đã vượt quá giới hạn yêu cầu truy cập")
        await redis.pipeline_incr_expire(key, self.period)
        return True


from src.core.infrastructure.mongo import mongo


async def get_db():
    return mongo.get_db()
