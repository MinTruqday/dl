from typing import Any, Dict, List, Optional
import httpx
import jwt
from core.config import settings
from core.database import db_client
from core.security import ALGORITHM, SECRET_KEY
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from loguru import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class AuthenticatedUser:
    def __init__(self, user_id: str, user_name: str = "User"):
        self.id = user_id
        self.full_name = user_name

async def get_db():
    return db_client.mongodb[settings.MONGODB_DB_NAME]

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        session_id: str = payload.get("sid")
        if email is None or session_id is None:
            logger.warning("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
            raise credentials_exception
    except jwt.PyJWTError:
        logger.warning("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        raise credentials_exception

    user_doc = None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.MANAGEMENT_URL}/nguoi-dung/thu-dien/{email}",
                timeout=settings.DEFAULT_HTTP_TIMEOUT,
            )
            if resp.status_code == 200:
                user_doc = resp.json().get("data")
    except Exception:
        pass

    if user_doc is None:
        logger.warning("Lỗi truy xuất cơ sở dữ liệu hệ thống")
        raise credentials_exception

    user_id_str = str(user_doc["_id"])

    if db_client.redis:
        is_valid_session = await db_client.redis.sismember(f"user_sessions:{user_id_str}", session_id)
        if not is_valid_session:
            logger.warning("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
            raise credentials_exception

    user_doc["_id"] = user_id_str
    user_doc["id"] = user_id_str
    return user_doc

async def get_current_user_optional(
    token: Optional[str] = Depends(OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False))
) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    try:
        return await get_current_user(token)
    except HTTPException:
        return None

async def get_current_user_token_param(token: str) -> Dict[str, Any]:
    return await get_current_user(token)

def require_role(required_roles: List[str]):
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if current_user.get("role") == "admin":
            return current_user
        if current_user.get("role") not in required_roles:
            logger.warning("Lỗi xử lý tài khoản")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Lỗi xử lý tài khoản",
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
                detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
            )
            
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        key = f"rate_limit:{client_ip}:{path}"
        
        current = await db_client.redis.get(key)
        if current is not None and int(current) >= self.calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
            )
            
        pipe = db_client.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.period)
        await pipe.execute()
        return True

def require_permissions(required_permissions: List[str]):
    async def permission_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_perms = current_user.get("permissions", [])
        if current_user.get("role") == "admin":
            return current_user
            
        missing = [p for p in required_permissions if p not in user_perms]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Lỗi xử lý tài khoản",
            )
        return current_user
    return permission_checker

def get_current_user_from_header(x_user_id: str = Header(None), x_user_name: str = Header("User")):
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"
        )
    return AuthenticatedUser(x_user_id, x_user_name)