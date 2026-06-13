import time
from typing import List, Optional

import jwt
from core.config import settings
from core.database import db_client
from core.schemas.user import RoleEnum, UserInDB
from core.security import ALGORITHM, SECRET_KEY
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from loguru import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_db():
    return db_client.mongodb[settings.MONGODB_DB_NAME]


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Phiên đăng nhập không hợp lệ hoặc đã hết hạn",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        session_id: str = payload.get("sid")
        if email is None or session_id is None:
            logger.warning("Dữ liệu giải mã token bị thiếu thông tin sub hoặc sid")
            raise credentials_exception
    except jwt.PyJWTError as e:
        logger.warning(f"Không thể giải mã JWT: {str(e)}")
        raise credentials_exception
    if db_client.redis:
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.PROVISION_URL}/user/internal/email/{email}",
                    timeout=3.0,
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
            logger.warning(f"Phát hiện nỗ lực dùng phiên bản cũ đã bị hủy của {email}")
            raise credentials_exception
    else:
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.PROVISION_URL}/user/internal/email/{email}",
                    timeout=3.0,
                )
                user_doc = resp.json().get("data") if resp.status_code == 200 else None
        except Exception:
            user_doc = None
    if user_doc is None:
        logger.warning(f"Không có người dùng nào sử dụng email {email}")
        raise credentials_exception
    user_id_str = str(user_doc["_id"])
    user_doc["_id"] = user_id_str
    return UserInDB(**user_doc)


async def get_current_user_optional(
    token: Optional[str] = Depends(
        OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)
    )
) -> Optional[UserInDB]:
    if not token:
        return None
    try:
        return await get_current_user(token)
    except HTTPException:
        return None


async def get_current_user_token_param(token: str) -> UserInDB:
    return await get_current_user(token)


def require_role(required_roles: List[RoleEnum]):

    async def role_checker(
        current_user: UserInDB = Depends(get_current_user),
    ) -> UserInDB:
        if current_user.role == RoleEnum.ADMIN:
            return current_user
        if current_user.role not in required_roles:
            logger.warning(
                f"Từ chối truy cập do {current_user.email} hiện có quyền {current_user.role} nhưng chức năng này yêu cầu quyền {required_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không hiện có quyền thực hiện thao tác này",
            )
        return current_user

    return role_checker


class RateLimiter:

    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period

    async def __call__(self, request: Request):
        if settings.MONGODB_DB_NAME == "doclib_test":
            return True
        if not db_client.redis:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Tính năng này đang bảo trì, vui lòng quay lại sau",
            )
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        key = f"rate_limit:{client_ip}:{path}"
        current = await db_client.redis.get(key)
        if current is not None and int(current) >= self.calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Thao tác quá nhanh, vui lòng thử lại sau",
            )
        pipe = db_client.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.period)
        await pipe.execute()
        return True


def require_permissions(required_permissions: List[str]):

    async def permission_checker(
        current_user: UserInDB = Depends(get_current_user),
    ) -> UserInDB:
        user_perms = current_user.permissions or []
        if current_user.role == RoleEnum.ADMIN:
            return current_user
        missing = [p for p in required_permissions if p not in user_perms]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Từ chối truy cập do thiếu quyền: {', '.join(missing)}",
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
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-User-ID header"
        )
    return AuthenticatedUser(x_user_id, x_user_name)
