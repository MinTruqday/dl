from fastapi import APIRouter, Depends, HTTPException

from src.core.dependency import verify_internal_token
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database


router = APIRouter(
    prefix="/xac-thuc/noi-bo",
    dependencies=[Depends(verify_internal_token)],
)


def account_view(credential: dict):
    account = {
        key: credential.get(key)
        for key in ["_id", "email", "slug", "full_name", "role", "permissions", "is_active", "storage_limit", "created_at", "updated_at"]
    }
    account.update(
        {
            "slug": credential.get("slug") or str(credential.get("email", "")).split("@", 1)[0],
            "full_name": credential.get("full_name") or "Người dùng DocLib",
            "role": credential.get("role", "reader"),
            "permissions": credential.get("permissions") or [],
            "is_active": credential.get("is_active", True),
            "storage_limit": credential.get("storage_limit") or 20 * 1024 * 1024 * 1024,
        }
    )
    return account


@router.get("/tai-khoan/{user_id}", include_in_schema=False)
async def get_account_by_id(user_id: str):
    credential = await database.mongodb[settings.AUTHENTICATION_DB_NAME].auth_credentials.find_one({"_id": user_id})
    if not credential:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
    return {"data": account_view(credential)}


@router.get("/tai-khoan/email/{email}", include_in_schema=False)
async def get_account_by_email(email: str):
    credential = await database.mongodb[settings.AUTHENTICATION_DB_NAME].auth_credentials.find_one({"email": email.lower()})
    if not credential:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
    return {"data": account_view(credential)}


@router.get("/bao-mat/{user_id}", include_in_schema=False)
async def get_security_state(user_id: str):
    credential = await database.mongodb[settings.AUTHENTICATION_DB_NAME].auth_credentials.find_one(
        {"_id": user_id},
        {"last_password_change": 1},
    )
    if not credential:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin bảo mật")
    return {"data": {"last_password_change": credential.get("last_password_change")}}
