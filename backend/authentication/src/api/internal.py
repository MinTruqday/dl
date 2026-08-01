from fastapi import APIRouter, Depends, HTTPException

from src.core.dependency import verify_internal_token
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database


router = APIRouter(
    prefix="/xac-thuc/noi-bo",
    dependencies=[Depends(verify_internal_token)],
)


@router.get("/bao-mat/{user_id}", include_in_schema=False)
async def get_security_state(user_id: str):
    credential = await database.mongodb[settings.AUTHENTICATION_DB_NAME].auth_credentials.find_one(
        {"_id": user_id},
        {"last_password_change": 1},
    )
    if not credential:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin bảo mật")
    return {"data": {"last_password_change": credential.get("last_password_change")}}
