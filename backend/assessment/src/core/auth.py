from enum import Enum

import hmac
import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field

from src.core.configuration import settings


class Role(str, Enum):
    GUEST = "guest"
    READER = "reader"
    AUTHOR = "author"
    ADMIN = "admin"


class CurrentUser(BaseModel):
    id: str = Field(alias="_id")
    email: str
    role: Role = Role.READER
    permissions: list[str] = Field(default_factory=list)

    @property
    def is_admin(self):
        return self.role == Role.ADMIN


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    x_test_user_id: str | None = Header(default=None),
    x_test_user_role: str = Header(default="author"),
):
    if settings.ASSESSMENT_ALLOW_TEST_IDENTITY and x_test_user_id:
        return CurrentUser(_id=x_test_user_id, email=f"{x_test_user_id}@test.local", role=x_test_user_role)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Yêu cầu xác thực")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("uid")
        email = payload.get("sub")
        if not user_id or not email:
            raise ValueError
        return CurrentUser(
            _id=user_id,
            email=email,
            role=payload.get("role", "reader"),
            permissions=payload.get("permissions", []),
        )
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Phiên đăng nhập không hợp lệ")


def require_admin(user: CurrentUser = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Yêu cầu quyền quản trị")
    return user


def require_author(user: CurrentUser = Depends(get_current_user)):
    if user.role not in {Role.AUTHOR, Role.ADMIN}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Yêu cầu quyền tác giả")
    return user


def require_internal_token(x_internal_token: str = Header(default="")):
    if not settings.SECRET_KEY or not x_internal_token or not hmac.compare_digest(x_internal_token, settings.SECRET_KEY):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Internal token không hợp lệ")
