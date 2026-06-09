from fastapi import Header, HTTPException
from src.schemas.user import UserInDB

async def get_current_user(x_user_id: str = Header(None)):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-Id header is missing")
    return UserInDB(_id=x_user_id)

async def get_db():
    from src.core.database import db_client
    return db_client.mongodb.get_default_database()
