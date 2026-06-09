from fastapi import Header, HTTPException, Query, Depends
from src.schemas.user import UserInDB
from typing import Optional

async def get_current_user(x_user_id: Optional[str] = Header(None)) -> UserInDB:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-Id header is missing")
    return UserInDB(_id=x_user_id)

async def get_current_user_from_token(token: str) -> UserInDB:
    import jwt
    from src.core.config import settings
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return UserInDB(_id=user_id)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_db():
    from src.core.database import db_client
    from src.core.config import settings
    return db_client.mongodb[settings.MONGODB_DB_NAME]
