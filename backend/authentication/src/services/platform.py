from datetime import datetime, timezone

from fastapi import Depends, HTTPException

from src.core.dependency import CurrentUser, SystemRole, get_current_user
from src.core.infrastructure.configuration import settings
from src.core.policies import platform_policy
from src.core.response import APIResponse
from src.repositories.identity import IdentityRepository


def account_view(credential):
    account = {
        key: credential.get(key)
        for key in [
            "_id",
            "email",
            "slug",
            "full_name",
            "system_role",
            "permissions",
            "is_active",
            "storage_limit",
            "created_at",
            "updated_at",
        ]
    }
    account.update(
        {
            "slug": credential.get("slug") or str(credential.get("email", "")).split("@", 1)[0],
            "full_name": credential.get("full_name") or "Người dùng Veriq",
            "system_role": credential.get("system_role", "USER"),
            "permissions": credential.get("permissions") or [],
            "is_active": credential.get("is_active", True),
            "storage_limit": credential.get("storage_limit")
            or settings.DEFAULT_STORAGE_LIMIT_BYTES,
        }
    )
    return account


async def account_or_404(user_id):
    account = await IdentityRepository.get_auth_credential_by_id(user_id)
    if not account:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
    return account


async def protect_last_admin(account, desired_role=None, desired_active=None):
    current_role = account.get("system_role", "USER")
    removing_admin = current_role == "ADMIN" and (desired_role == "USER" or desired_active is False)
    if not removing_admin:
        return
    active_admins = await IdentityRepository.count_auth_credentials(
        {"is_active": {"$ne": False}, "system_role": "ADMIN"}
    )
    if active_admins <= 1:
        raise HTTPException(status_code=422, detail="Không thể vô hiệu hóa quản trị viên cuối cùng")


async def record_audit(current_user, action, user_id, reason, details=None):
    await IdentityRepository.insert_audit_log(
        {
            "action": action,
            "actor_email": current_user.email,
            "target_user_id": user_id,
            "reason": reason,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc),
        }
    )


async def require_system_admin(current_user: CurrentUser = Depends(get_current_user)):
    if current_user.system_role != SystemRole.ADMIN:
        raise HTTPException(status_code=403, detail="Chức năng chỉ dành cho quản trị hệ thống")
    return current_user


def masked_config(config):
    policy = platform_policy()["configuration"]
    data = {key: value for key, value in config.items() if key not in {"_id", "type"}}
    for key in list(data):
        if any(marker in key.lower() for marker in policy["sensitive_key_markers"]):
            data[key] = "Đã cấu hình" if data[key] else None
    return data


async def get_platform_config(config_type, current_user):
    config = await IdentityRepository.get_system_config_by_type(config_type)
    await record_audit(current_user, "ADMIN_CONFIG_VIEWED", config_type, "platform configuration")
    return APIResponse(
        data=masked_config(config or {"type": config_type}),
        message="Tải cấu hình nền tảng hoàn tất",
    )


async def update_platform_config(config_type, payload, current_user):
    maximum_key_characters = platform_policy()["configuration"]["maximum_key_characters"]
    allowed = {
        key: value
        for key, value in payload.values.items()
        if isinstance(key, str) and len(key) <= maximum_key_characters
    }
    if not allowed:
        raise HTTPException(status_code=422, detail="Không có cấu hình hợp lệ")
    timestamp = datetime.now(timezone.utc)
    await IdentityRepository.update_system_config(
        config_type,
        {
            "$set": {**allowed, "updated_at": timestamp, "updated_by": current_user.id},
            "$setOnInsert": {"type": config_type, "created_at": timestamp},
        },
        upsert=True,
    )
    await record_audit(
        current_user, "ADMIN_CONFIG_UPDATED", config_type, payload.reason, {"keys": sorted(allowed)}
    )
    return await get_platform_config(config_type, current_user)
