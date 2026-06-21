import time
from typing import List, Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from loguru import logger

from core.config import settings
from core.database import db_client

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class RoleEnum(str, Enum):
    GUEST = "guest"
    READER = "reader"
    AUTHOR = "author"
    ADMIN = "admin"

class CurrentUser(BaseModel):
    id: str = Field(alias="_id")
    email: str
    role: RoleEnum = RoleEnum.READER
    permissions: List[str] = []
    is_active: bool = True
    full_name: str = ""
    is_premium: bool = False
    
    class Config:
        populate_by_name = True
        extra = "ignore"

from core.security import ALGORITHM, SECRET_KEY

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_db():
    return db_client.mongodb[settings.SERVICE_DB_NAME]


async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        session_id: str = payload.get("sid")
        if email is None or session_id is None:
            logger.warning("Lỗi xác minh mã thông báo do thiếu thông tin")
            raise credentials_exception
    except jwt.PyJWTError:
        logger.warning("Lỗi giải mã xác thực do dữ liệu không hợp lệ")
        raise credentials_exception
    if db_client.redis:
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.MANAGEMENT_URL}/nguoi-dung/email/{email}",
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                user_doc = resp.json().get("data") if resp.status_code == 200 else None
        except Exception:
            user_doc = None
        if not user_doc:
            raise credentials_exception
        user_id_str = str(user_doc["_id"])
        is_valid_session = await db_client.redis.sismember(
            f"user_sessions:{user_id_str}", session_id
        )
        if not is_valid_session:
            logger.warning("Ngăn chặn truy cập phiên đăng nhập đã hủy")
            raise credentials_exception
    else:
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.MANAGEMENT_URL}/nguoi-dung/email/{email}",
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                user_doc = resp.json().get("data") if resp.status_code == 200 else None
        except Exception:
            user_doc = None
    if user_doc is None:
        logger.warning("Không tìm thấy tài khoản với thông tin đăng nhập")
        raise credentials_exception
    user_id_str = str(user_doc["_id"])
    user_doc["_id"] = user_id_str
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


def require_role(required_roles: List[RoleEnum]):

    async def role_checker(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if current_user.role == RoleEnum.ADMIN:
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
        if not db_client.redis:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Tính năng đang bảo trì, vui lòng thử lại sau",
            )
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        key = f"rate_limit:{client_ip}:{path}"
        current = await db_client.redis.get(key)
        if current is not None and int(current) >= self.calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Vượt quá giới hạn yêu cầu, tạm thời bị hạn chế truy cập",
            )
        pipe = db_client.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.period)
        await pipe.execute()
        return True


def require_permissions(required_permissions: List[str]):

    async def permission_checker(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        user_perms = current_user.permissions or []
        if current_user.role == RoleEnum.ADMIN:
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
