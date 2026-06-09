from fastapi import Header, HTTPException, Depends
from typing import Optional, List
from src.schemas.user import UserInDB, RoleEnum
import jwt

async def get_current_user(x_user_id: Optional[str] = Header(None), x_user_role: Optional[str] = Header(None)) -> UserInDB:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-Id header is missing")
    try:
        role = RoleEnum(x_user_role) if x_user_role else RoleEnum.READER
    except ValueError:
        role = RoleEnum.READER
    return UserInDB(**{"_id": x_user_id, "role": role})

def require_role(roles: List[RoleEnum]):
    async def _check(current_user: UserInDB = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Không có quyền truy cập")
        return current_user
    return _check

async def get_db():
    from src.core.database import db_client
    from src.core.config import settings
    return db_client.mongodb[settings.MONGODB_DB_NAME]
