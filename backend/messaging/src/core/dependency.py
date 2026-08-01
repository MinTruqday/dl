import hmac
from enum import Enum
from typing import Any, List, Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from loguru import logger

from src.core.infrastructure.configuration import settings
from pydantic import BaseModel, ConfigDict, Field, field_validator
from src.core.infrastructure.redis import redis

class Role(str, Enum):
    GUEST = "guest"
    READER = "reader"
    AUTHOR = "author"
    ADMIN = "admin"

class Tier(str, Enum):
    BASIC = "basic"
    PRO = "pro"
    PREMIUM = "premium"

class CurrentUser(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str = Field(alias="_id")
    email: str
    role: Role = Role.READER
    permissions: List[str] = Field(default_factory=list)
    is_active: bool = True
    full_name: str = ""
    slug: str = ""
    is_premium: bool = False
    ai_tier: str = "basic"
    
    @field_validator("role", mode="before")
    @classmethod
    def validate_role_case(cls, v: Any):
        if isinstance(v, str):
            return v.lower()
        return v

    @field_validator("ai_tier", mode="before")
    @classmethod
    def validate_tier_case(cls, v: Any):
        if isinstance(v, str):
            return v.lower()
        return v

    def is_admin(self) -> bool:
        role_val = self.role.value if hasattr(self.role, "value") else str(self.role).lower()
        return role_val == Role.ADMIN.value

    def has_ai_access(self) -> bool:
        if self.is_admin():
            return True
        tier_val = str(self.ai_tier).lower()
        return tier_val in [Tier.PRO.value, Tier.PREMIUM.value]

    
ALGORITHM = "HS256"
SECRET_KEY = settings.SECRET_KEY

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Phiên đăng nhập đã quá hạn sử dụng, vui lòng thực hiện xác thực lại",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        session_id: str = payload.get("sid")
        if email is None or session_id is None:
            logger.warning("Token verification failed due to missing identity claims")
            raise credentials_exception
    except jwt.PyJWTError as e:
        logger.exception("Authentication token decoding failed due to malformed payload")
        raise credentials_exception

    uid = payload.get("uid")
    if not uid:
        logger.warning("Missing user identifier (UID) in authentication token")
        raise credentials_exception

    is_valid_session = await redis.sismember(
        f"user_sessions:{uid}", session_id
    )
    if not is_valid_session:
        logger.warning("Attempted to use an invalidated or revoked session token")
        raise credentials_exception

    user_doc = {
        "_id": uid,
        "email": email,
        "role": payload.get("role", "reader"),
        "permissions": payload.get("permissions", []),
        "is_premium": payload.get("is_premium", False),
        "full_name": payload.get("full_name", ""),
        "slug": payload.get("slug", ""),
        "is_active": True,
        "ai_tier": payload.get("ai_tier", "BASIC"),
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
            logger.warning("Access denied due to insufficient authorization privileges")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản không có đủ thẩm quyền để thực hiện hành động này",
            )
        return current_user

    return role_checker

class RateLimiting:

    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period

    async def __call__(self, request: Request):

        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        key = f"rate_limit:{client_ip}:{path}"
        current = await redis.get(key)
        if current is not None and int(current) >= self.calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Vượt quá giới hạn số lượng yêu cầu truy cập cho phép, hệ thống tạm thời hạn chế truy cập",
            )
        await redis.pipeline_incr_expire(key, self.period)
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
                detail="Tài khoản không được cấp quyền hạn tương ứng cho chức năng này",
            )
        return current_user

    return permission_checker

from fastapi import Header

async def verify_internal_token(x_internal_token: str = Header(default="")):
    if not hmac.compare_digest(x_internal_token, settings.SECRET_KEY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mã xác thực nội bộ không hợp lệ",
        )

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
            detail="Yêu cầu truy cập không cung cấp đầy đủ thông tin định danh",
        )
    return AuthenticatedUser(x_user_id, x_user_name)


from src.core.infrastructure.mongo import mongo

async def get_db():
    return mongo.get_db()
