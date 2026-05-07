from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
import jwt
from core.security import SECRET_KEY, ALGORITHM
from core.database import db_client
from models.user import UserInDB, RoleEnum
import time
from core.config import settings
from loguru import logger
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
async def get_db():
    return db_client.mongodb[settings.MONGODB_DB_NAME]
async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Phiên đăng nhập không hợp lệ hoặc đã hết hạn.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        session_id: str = payload.get("sid")
        if email is None:
            logger.warning(f"Token payload missing 'sub' (email)")
            raise credentials_exception
    except jwt.PyJWTError as e:
        logger.warning(f"JWT Decode error: {str(e)}")
        raise credentials_exception
    user_doc = await db_client.mongodb[settings.MONGODB_DB_NAME]["users"].find_one({"email": email})
    if user_doc is None:
        logger.warning(f"User not found for email: {email}")
        raise credentials_exception
    user_id_str = str(user_doc["_id"])
    user_doc["_id"] = user_id_str
    return UserInDB(**user_doc)
async def get_current_user_optional(token: Optional[str] = Depends(OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False))) -> Optional[UserInDB]:
    if not token:
        return None
    try:
        return await get_current_user(token)
    except HTTPException:
        return None
async def get_current_user_token_param(token: str) -> UserInDB:
    return await get_current_user(token)
def require_role(required_roles: List[RoleEnum]):
    async def role_checker(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
        if current_user.role == RoleEnum.ADMIN:
            return current_user
        if current_user.role not in required_roles:
            logger.warning(f"Role Access Denied: User {current_user.email} has role {current_user.role}, but need {required_roles}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền thực hiện thao tác này."
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
                detail="Tính năng này đang bảo trì, vui lòng quay lại sau."
            )
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        key = f"rate_limit:{client_ip}:{path}"
        current = await db_client.redis.get(key)
        if current is not None and int(current) >= self.calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Thao tác quá nhanh, vui lòng thử lại sau."
            )
        pipe = db_client.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.period)
        await pipe.execute()
        return True
def require_permissions(required_permissions: List[str]):
    async def permission_checker(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
        user_perms = current_user.permissions or []
        if current_user.role == RoleEnum.ADMIN:
            return current_user
        missing = [p for p in required_permissions if p not in user_perms]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Quyền bị từ chối. Thiếu quyền: {', '.join(missing)}"
            )
        return current_user
    return permission_checker
