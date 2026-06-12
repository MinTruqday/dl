from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
import jwt
from core.security import SECRET_KEY, ALGORITHM
from core.database import db_client
from src.schemas.user import UserInDB, RoleEnum
from core.config import settings
from loguru import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/login')

async def get_db():
    return db_client.mongodb[settings.MONGODB_DB_NAME]

async def get_current_user(token: str=Depends(oauth2_scheme)) -> UserInDB:
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Phiên làm việc đã hết hạn hoặc không hợp lệ', headers={'WWW-Authenticate': 'Bearer'})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get('sub')
        session_id: str = payload.get('sid')
        if email is None or session_id is None:
            logger.warning(f"Dữ liệu token bị thiếu trường sub hoặc sid")
            raise credentials_exception
    except jwt.PyJWTError as e:
        logger.warning(f'Phiên đăng nhập không hợp lệ {str(e)}')
        raise credentials_exception
    if db_client.redis:
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{settings.PROVISION_URL}/nguoi-dung/noi-bo/email/{email}", timeout=3.0)
                user_doc = resp.json().get('data') if resp.status_code == 200 else None
        except Exception:
            user_doc = None
        if not user_doc:
            raise credentials_exception
        user_id_str = str(user_doc['_id'])
        is_valid_session = await db_client.redis.sismember(f'user_sessions:{user_id_str}', session_id)
        if not is_valid_session:
            logger.warning(f'Phát hiện nỗ lực sử dụng phiên làm việc cũ của {email}')
            raise credentials_exception
    else:
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{settings.PROVISION_URL}/nguoi-dung/noi-bo/email/{email}", timeout=3.0)
                user_doc = resp.json().get('data') if resp.status_code == 200 else None
        except Exception:
            user_doc = None
    if user_doc is None:
        logger.warning(f'Hệ thống không tìm thấy tài khoản nào sử dụng email {email}')
        raise credentials_exception
    user_id_str = str(user_doc['_id'])
    user_doc['_id'] = user_id_str
    return UserInDB(**user_doc)

async def get_current_user_optional(token: Optional[str]=Depends(OAuth2PasswordBearer(tokenUrl='auth/login', auto_error=False))) -> Optional[UserInDB]:
    if not token:
        return None
    try:
        return await get_current_user(token)
    except HTTPException:
        return None

def require_role(required_roles: List[RoleEnum]):
    async def role_checker(current_user: UserInDB=Depends(get_current_user)) -> UserInDB:
        if current_user.role == RoleEnum.ADMIN:
            return current_user
        if current_user.role not in required_roles:
            logger.warning(f'Tài khoản {current_user.email} có quyền {current_user.role} nhưng tính năng này yêu cầu quyền {required_roles}')
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Bạn không có quyền thực hiện thao tác này')
        return current_user
    return role_checker
