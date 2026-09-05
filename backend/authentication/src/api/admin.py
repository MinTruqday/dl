import re
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator
from pymongo import ReturnDocument

from src.api.internal import account_view
from src.core.dependency import CurrentUser, Role, SystemRole, get_current_user, require_role
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.response import APIResponse
from src.repositories.identity import IdentityRepository


class AdminAccountUpdate(BaseModel):
    role: Role | None = None
    system_role: SystemRole | None = None
    is_active: bool | None = None
    reason: str = Field(min_length=3, max_length=1000)

    @model_validator(mode="after")
    def validate_change(self):
        if self.role is None and self.system_role is None and self.is_active is None:
            raise ValueError("Cần cung cấp thay đổi vai trò hoặc trạng thái")
        return self


router = APIRouter(prefix="/quan-tri", tags=["Quản trị tài khoản"], dependencies=[Depends(require_role([Role.ADMIN]))])


@router.get("/tai-khoan", response_model=APIResponse[Any])
async def list_accounts(
    search: str | None = None,
    role: Role | None = None,
    system_role: SystemRole | None = None,
    is_active: bool | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
):
    query: dict[str, Any] = {}
    if search:
        pattern = re.escape(search.strip())
        query["$or"] = [
            {"email": {"$regex": pattern, "$options": "i"}},
            {"slug": {"$regex": pattern, "$options": "i"}},
            {"full_name": {"$regex": pattern, "$options": "i"}},
        ]
    if role is not None:
        query["role"] = role.value
    if system_role is not None:
        query["system_role"] = system_role.value
    if is_active is not None:
        query["is_active"] = is_active
    accounts = (
        await database.mongodb[settings.AUTHENTICATION_DB_NAME]
        .auth_credentials.find(query)
        .sort("created_at", -1)
        .limit(limit)
        .to_list(limit)
    )
    return APIResponse(
        data=[account_view(account) for account in accounts],
        message="Tải danh sách tài khoản hoàn tất",
    )


@router.patch("/tai-khoan/{user_id}", response_model=APIResponse[Any])
async def update_account(
    user_id: str, payload: AdminAccountUpdate, current_user: CurrentUser = Depends(get_current_user)
):
    if user_id == current_user.id and (
        payload.is_active is False
        or payload.role not in {None, Role.ADMIN}
        or payload.system_role not in {None, SystemRole.ADMIN}
    ):
        raise HTTPException(
            status_code=422, detail="Không thể tự khóa hoặc hạ quyền tài khoản quản trị hiện tại"
        )
    changes = {
        key: value.value if isinstance(value, (Role, SystemRole)) else value
        for key, value in payload.model_dump(exclude={"reason"}).items()
        if value is not None
    }
    changes["updated_at"] = datetime.now(timezone.utc)
    account = await database.mongodb[
        settings.AUTHENTICATION_DB_NAME
    ].auth_credentials.find_one_and_update(
        {"_id": user_id}, {"$set": changes}, return_document=ReturnDocument.AFTER
    )
    if not account:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
    await IdentityRepository.revoke_all_sessions(user_id)
    await IdentityRepository.insert_audit_log(
        {
            "action": "ADMIN_ACCOUNT_UPDATED",
            "actor_email": current_user.email,
            "target_user_id": user_id,
            "changes": changes,
            "reason": payload.reason,
            "timestamp": changes["updated_at"],
        }
    )
    return APIResponse(
        data=account_view(account), message="Cập nhật tài khoản và thu hồi phiên hoàn tất"
    )


@router.get("/nhat-ky", response_model=APIResponse[Any])
async def list_auth_audit(
    action: str | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    current_user: CurrentUser = Depends(get_current_user),
):
    query = {"action": action} if action else {}
    events = (
        await database.mongodb[settings.AUTHENTICATION_DB_NAME]
        .audit_logs.find(query)
        .sort("timestamp", -1)
        .limit(limit)
        .to_list(limit)
    )
    return APIResponse(
        data=[{**event, "_id": str(event["_id"])} for event in events],
        message="Tải nhật ký xác thực hoàn tất",
    )
