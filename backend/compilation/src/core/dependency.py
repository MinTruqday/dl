from enum import Enum

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.redis import redis


class Role(str, Enum):
    GUEST = "guest"
    READER = "reader"
    AUTHOR = "author"
    ADMIN = "admin"


class CurrentUser(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str = Field(alias="_id")
    email: str
    role: Role = Role.READER
    permissions: list[str] = Field(default_factory=list)

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, value):
        return value.lower() if isinstance(value, str) else value

    @property
    def is_admin(self):
        return self.role == Role.ADMIN


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/xac-thuc/dang-nhap")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Phiên đăng nhập không hợp lệ hoặc đã hết hạn",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("uid")
        email = payload.get("sub")
        session_id = payload.get("sid")
        if not user_id or not email or not session_id:
            raise credentials_error
    except jwt.PyJWTError:
        raise credentials_error
    if not await redis.sismember(f"user_sessions:{user_id}", session_id):
        raise credentials_error
    return CurrentUser(
        _id=user_id,
        email=email,
        role=payload.get("role", "reader"),
        permissions=payload.get("permissions", []),
    )
