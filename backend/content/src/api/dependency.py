from fastapi import Header, HTTPException
from typing import Optional
from src.schemas.user import UserInDB, RoleEnum

async def get_current_user(x_user_id: Optional[str] = Header(None)) -> UserInDB:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-Id header is missing")
    return UserInDB(_id=x_user_id)

async def require_role(roles: list):
    async def checker(x_user_id: Optional[str] = Header(None), x_user_role: Optional[str] = Header(None)):
        if not x_user_id:
            raise HTTPException(status_code=401, detail="Chưa xác thực")
        if x_user_role not in [r.value if hasattr(r, 'value') else r for r in roles]:
            raise HTTPException(status_code=403, detail="Không có quyền truy cập")
        return UserInDB(_id=x_user_id)
    return checker

async def get_db():
    from src.core.database import db_client
    from src.core.config import settings
    return db_client.mongodb[settings.MONGODB_DB_NAME]
