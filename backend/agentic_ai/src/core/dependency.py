from src.core.infrastructure.redis_client import redis_client
import time
from typing import List, Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from loguru import logger

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class Role(str, Enum):
    GUEST = "guest"
    READER = "reader"
    AUTHOR = "author"
    ADMIN = "admin"

class CurrentUser(BaseModel):
    id: str = Field(alias="_id")
    email: str
    role: Role = Role.READER
    permissions: List[str] = []
    is_active: bool = True
    full_name: str = ""
    slug: str = ""
    is_premium: bool = False
    
    from pydantic import field_validator
    @field_validator("role", mode="before")
    @classmethod
    def validate_role_case(cls, v: Any):
        if isinstance(v, str):
            return v.lower()
        return v
    
    class Config:
        populate_by_name = True
        extra = "ignore"

from src.core.security.access import ALGORITHM, SECRET_KEY

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Phiên đăng nhập của bạn đã quá hạn an toàn, vui lòng tiến hành đăng nhập lại",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        session_id: str = payload.get("sid")
        if email is None or session_id is None:
            logger.warning("Lỗi xác minh mã thông báo do thiếu thông tin")
            raise credentials_exception
    except jwt.PyJWTError as e:
        logger.warning(f"Lỗi giải mã xác thực do dữ liệu không hợp lệ: {e}")
        raise credentials_exception

    uid = payload.get("uid")
    if not uid:
        logger.warning("Thiếu UID trong token")
        raise credentials_exception

    is_valid_session = await redis_client.sismember(
        f"user_sessions:{uid}", session_id
    )
    if not is_valid_session:
        logger.warning("Ngăn chặn truy cập phiên đăng nhập đã hủy")
        raise credentials_exception

    user_doc = {
        "_id": uid,
        "email": email,
        "role": payload.get("role", "reader"),
        "permissions": payload.get("permissions", []),
        "is_premium": payload.get("is_premium", False),
        "full_name": payload.get("full_name", ""),
        "slug": payload.get("slug", ""),
        "is_active": True
    }
    return CurrentUser(**user_doc)


async def get_current_user_optional(
    token: Optional[str] = Depends(
        OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)
    )
) -> Optional[CurrentUser]:
    if not token:
        return None
    try:
        return await get_current_user(token)
    except HTTPException:
        return None


async def get_current_user_token_param(token: str) -> CurrentUser:
    return await get_current_user(token)


def require_role(required_roles: List[Role]):

    async def role_checker(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if current_user.role == Role.ADMIN:
            return current_user
        if current_user.role not in required_roles:
            logger.warning("Từ chối truy cập do không đủ ủy quyền")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Không có quyền thực hiện thao tác này",
            )
        return current_user

    return role_checker


class RateLimiting:

    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period

    async def __call__(self, request: Request):
        if settings.SERVICE_DB_NAME == "doclib_test":
            return True

        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        key = f"rate_limit:{client_ip}:{path}"
        current = await redis_client.get(key)
        if current is not None and int(current) >= self.calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Vượt quá giới hạn yêu cầu, tạm thời bị hạn chế truy cập",
            )
        await redis_client.pipeline_incr_expire(key, self.period)
        return True


def require_permissions(required_permissions: List[str]):

    async def permission_checker(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        user_perms = current_user.permissions or []
        if current_user.role == Role.ADMIN:
            return current_user
        missing = [p for p in required_permissions if p not in user_perms]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Thao tác bị từ chối do không đủ quyền",
            )
        return current_user

    return permission_checker


from fastapi import Header


class AuthenticatedUser:
    def __init__(self, user_id: str, user_name: str = "User"):
        self.id = user_id
        self.full_name = user_name


def get_current_user_from_header(
    x_user_id: str = Header(None), x_user_name: str = Header("User")
):
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thiếu thông tin định danh người dùng",
        )
    return AuthenticatedUser(x_user_id, x_user_name)
