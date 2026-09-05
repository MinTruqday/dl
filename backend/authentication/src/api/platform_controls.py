import hashlib
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, EmailStr, Field, model_validator
from pymongo import ReturnDocument

from src.api.platform import (
    ActionReason,
    ConfigUpdate,
    account_or_404,
    get_platform_config,
    protect_last_admin,
    record_audit,
    require_system_admin,
    update_platform_config,
)
from src.core.dependency import CurrentUser, get_current_user
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.infrastructure.redis import redis
from src.core.response import APIResponse
from src.repositories.identity import IdentityRepository
from src.services.email import EmailService
from src.services.session import SessionService


class UserDeleteRequest(BaseModel):
    confirmation: str = Field(min_length=1, max_length=320)
    reason: str = Field(min_length=3, max_length=1000)


class BulkUserPreviewRequest(BaseModel):
    action: Literal["DISABLE", "INVITE", "REVOKE_SESSIONS"]
    user_ids: list[str] = Field(min_length=1, max_length=500)
    reason: str = Field(min_length=3, max_length=1000)


class BulkUserConfirmRequest(BaseModel):
    confirmation: Literal["CONFIRM"]


class ProjectDeleteRequest(BaseModel):
    confirmation: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=3, max_length=1000)


class BreakGlassCreateRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=128)
    user_id: str = Field(min_length=1, max_length=128)
    permissions: list[str] = Field(min_length=1, max_length=100)
    ttl_minutes: int = Field(ge=5, le=240)
    reason: str = Field(min_length=10, max_length=1000)


class ServiceIdentityRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    secret_reference: str = Field(min_length=1, max_length=500)
    scopes: list[str] = Field(default_factory=list, max_length=100)
    reason: str = Field(min_length=3, max_length=1000)


class ServiceIdentityRotateRequest(BaseModel):
    secret_reference: str = Field(min_length=1, max_length=500)
    reason: str = Field(min_length=3, max_length=1000)


class SecretReferenceRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    provider: str = Field(min_length=2, max_length=100)
    reference: str = Field(min_length=1, max_length=500)
    reason: str = Field(min_length=3, max_length=1000)


class SecretReferenceRotateRequest(BaseModel):
    reference: str = Field(min_length=1, max_length=500)
    reason: str = Field(min_length=3, max_length=1000)


class EmergencyRevokeRequest(BaseModel):
    scope: Literal["USER", "ALL_USERS", "SERVICE_IDENTITY", "ALL_SERVICE_IDENTITIES"]
    target_id: str | None = Field(default=None, max_length=128)
    confirmation: Literal["EMERGENCY_REVOKE"]
    reason: str = Field(min_length=10, max_length=1000)

    @model_validator(mode="after")
    def validate_target(self):
        if self.scope in {"USER", "SERVICE_IDENTITY"} and not self.target_id:
            raise ValueError("Cần cung cấp đối tượng cần thu hồi")
        return self


class SmtpTestRequest(BaseModel):
    recipient: EmailStr
    reason: str = Field(min_length=3, max_length=1000)


class RagReindexRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=128)
    artifact_version_ids: list[str] = Field(default_factory=list, max_length=1000)
    reason: str = Field(min_length=3, max_length=1000)


class CacheClearRequest(BaseModel):
    scope: Literal["RATE_LIMITS", "PASSKEY_CHALLENGES", "PROJECT_METADATA", "SAFE_ALL"]
    confirmation: Literal["CLEAR_SAFE_CACHE"]
    reason: str = Field(min_length=3, max_length=1000)


class MaintenanceModeRequest(BaseModel):
    enabled: bool
    banner: str = Field(default="", max_length=500)
    reason: str = Field(min_length=3, max_length=1000)


router = APIRouter(
    prefix="/quan-tri",
    tags=["Quản trị nền tảng"],
    dependencies=[Depends(require_system_admin)],
)


def masked_reference(value: dict):
    return {
        **{
            key: item for key, item in value.items() if key not in {"reference", "secret_reference"}
        },
        **({"reference": "Đã cấu hình"} if value.get("reference") else {}),
        **({"secret_reference": "Đã cấu hình"} if value.get("secret_reference") else {}),
    }


@router.post("/tai-khoan/{user_id}/gui-lai-xac-minh", response_model=APIResponse[Any])
async def resend_account_activation(
    user_id: str,
    payload: ActionReason,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
):
    account = await account_or_404(user_id)
    await SessionService.forgot_password(
        account["email"], request.client.host if request.client else "admin"
    )
    await record_audit(current_user, "ADMIN_USER_ACTIVATION_RESENT", user_id, payload.reason)
    return APIResponse(
        data={"user_id": user_id, "delivery_status": "ACCEPTED"},
        message="Gửi lại quy trình kích hoạt tài khoản hoàn tất",
    )


@router.delete("/tai-khoan/{user_id}", response_model=APIResponse[Any])
async def anonymize_user(
    user_id: str, payload: UserDeleteRequest, current_user: CurrentUser = Depends(get_current_user)
):
    account = await account_or_404(user_id)
    if payload.confirmation != account.get("email"):
        raise HTTPException(status_code=422, detail="Xác nhận phải khớp email tài khoản")
    if user_id == current_user.id:
        raise HTTPException(status_code=422, detail="Không thể tự xóa tài khoản quản trị hiện tại")
    await protect_last_admin(account, desired_active=False)
    timestamp = datetime.now(timezone.utc)
    digest = hashlib.sha256(f"{user_id}:{timestamp.isoformat()}".encode()).hexdigest()[:24]
    await database.mongodb[settings.AUTHENTICATION_DB_NAME].auth_credentials.update_one(
        {"_id": user_id},
        {
            "$set": {
                "email": f"deleted-{digest}@invalid.local",
                "slug": f"deleted-{digest}",
                "full_name": "Tài khoản đã xóa",
                "is_active": False,
                "account_status": "DELETED",
                "system_role": "USER",
                "role": "reader",
                "permissions": [],
                "passkeys": [],
                "deleted_at": timestamp,
                "deleted_by": current_user.id,
                "updated_at": timestamp,
            },
            "$unset": {
                "password_hash": "",
                "bio": "",
                "avatar_url": "",
                "social_links": "",
                "donation_link": "",
            },
        },
    )
    await IdentityRepository.revoke_all_sessions(user_id)
    await record_audit(current_user, "ADMIN_USER_ANONYMIZED", user_id, payload.reason)
    return APIResponse(
        data={"user_id": user_id, "status": "DELETED", "anonymized": True},
        message="Ẩn danh và vô hiệu hóa tài khoản hoàn tất",
    )


@router.post("/tai-khoan/hang-loat/xem-truoc", response_model=APIResponse[Any], status_code=201)
async def preview_bulk_user_action(
    payload: BulkUserPreviewRequest, current_user: CurrentUser = Depends(get_current_user)
):
    user_ids = list(dict.fromkeys(payload.user_ids))
    accounts = (
        await database.mongodb[settings.AUTHENTICATION_DB_NAME]
        .auth_credentials.find(
            {"_id": {"$in": user_ids}}, {"email": 1, "is_active": 1, "account_status": 1}
        )
        .to_list(len(user_ids))
    )
    operation = {
        "_id": f"bulk-user-{uuid4().hex}",
        "kind": "USER_BULK_ACTION",
        "action": payload.action,
        "user_ids": [item["_id"] for item in accounts],
        "requested_user_ids": user_ids,
        "missing_user_ids": sorted(set(user_ids) - {item["_id"] for item in accounts}),
        "reason": payload.reason,
        "status": "PREVIEW_READY",
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=15),
    }
    await database.mongodb[settings.AUTHENTICATION_DB_NAME].admin_operations.insert_one(operation)
    return APIResponse(
        data={**operation, "accounts": accounts},
        message="Tạo bản xem trước thao tác hàng loạt hoàn tất",
        status=201,
    )


@router.post("/tai-khoan/hang-loat/{operation_id}/xac-nhan", response_model=APIResponse[Any])
async def confirm_bulk_user_action(
    operation_id: str,
    payload: BulkUserConfirmRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    operation = await database.mongodb[
        settings.AUTHENTICATION_DB_NAME
    ].admin_operations.find_one_and_update(
        {
            "_id": operation_id,
            "kind": "USER_BULK_ACTION",
            "status": "PREVIEW_READY",
            "created_by": current_user.id,
            "expires_at": {"$gt": datetime.now(timezone.utc)},
        },
        {"$set": {"status": "APPLYING", "confirmed_at": datetime.now(timezone.utc)}},
        return_document=ReturnDocument.AFTER,
    )
    if not operation:
        raise HTTPException(
            status_code=409, detail="Bản xem trước không tồn tại đã hết hạn hoặc đã dùng"
        )
    user_ids = [item for item in operation["user_ids"] if item != current_user.id]
    affected = 0
    if operation["action"] == "DISABLE":
        accounts = (
            await database.mongodb[settings.AUTHENTICATION_DB_NAME]
            .auth_credentials.find({"_id": {"$in": user_ids}})
            .to_list(len(user_ids))
        )
        for account in accounts:
            await protect_last_admin(account, desired_active=False)
        result = await database.mongodb[
            settings.AUTHENTICATION_DB_NAME
        ].auth_credentials.update_many(
            {"_id": {"$in": user_ids}},
            {
                "$set": {
                    "is_active": False,
                    "account_status": "DISABLED",
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        affected = result.modified_count
        for user_id in user_ids:
            await IdentityRepository.revoke_all_sessions(user_id)
    elif operation["action"] == "REVOKE_SESSIONS":
        for user_id in user_ids:
            await IdentityRepository.revoke_all_sessions(user_id)
            affected += 1
    else:
        accounts = (
            await database.mongodb[settings.AUTHENTICATION_DB_NAME]
            .auth_credentials.find({"_id": {"$in": user_ids}}, {"email": 1})
            .to_list(len(user_ids))
        )
        for account in accounts:
            await SessionService.forgot_password(account["email"], "admin-bulk")
            affected += 1
    await database.mongodb[settings.AUTHENTICATION_DB_NAME].admin_operations.update_one(
        {"_id": operation_id},
        {
            "$set": {
                "status": "COMPLETED",
                "affected": affected,
                "completed_at": datetime.now(timezone.utc),
            }
        },
    )
    await record_audit(
        current_user,
        "ADMIN_USER_BULK_COMPLETED",
        operation_id,
        operation["reason"],
        {"action": operation["action"], "affected": affected},
    )
    return APIResponse(
        data={"operation_id": operation_id, "status": "COMPLETED", "affected": affected},
        message="Hoàn tất thao tác tài khoản hàng loạt",
    )


@router.get("/du-an/{project_id}/vai-tro-du-an", response_model=APIResponse[Any])
async def project_membership_diagnostics(
    project_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    testing_db = database.mongodb[os.environ.get("TESTING_DB_NAME", "veriq_testing")]
    if not await testing_db.projects.find_one({"_id": project_id}, {"_id": 1}):
        raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
    memberships = (
        await testing_db.project_members.find(
            {"project_id": project_id},
            {
                "user_id": 1,
                "project_role": 1,
                "status": 1,
                "membership_revision": 1,
                "created_at": 1,
                "updated_at": 1,
            },
        )
        .sort("updated_at", -1)
        .to_list(10000)
    )
    await record_audit(
        current_user, "ADMIN_PROJECT_MEMBERSHIPS_VIEWED", project_id, "support metadata"
    )
    return APIResponse(data=memberships, message="Tải chẩn đoán thành viên dự án hoàn tất")


@router.delete("/du-an/{project_id}", response_model=APIResponse[Any])
async def hard_delete_project(
    project_id: str,
    payload: ProjectDeleteRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    testing_db = database.mongodb[os.environ.get("TESTING_DB_NAME", "veriq_testing")]
    project = await testing_db.projects.find_one({"_id": project_id}, {"key": 1, "name": 1})
    if not project:
        raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
    if payload.confirmation != project.get("key"):
        raise HTTPException(status_code=422, detail="Xác nhận phải khớp mã dự án")
    deleted = {}
    for collection_name in await testing_db.list_collection_names():
        if collection_name in {"audit_events", "counters"}:
            continue
        result = await testing_db[collection_name].delete_many({"project_id": project_id})
        if result.deleted_count:
            deleted[collection_name] = result.deleted_count
    await testing_db.audit_events.update_many(
        {"project_id": project_id}, {"$set": {"project_deleted": True}, "$unset": {"details": ""}}
    )
    await testing_db.counters.delete_many({"_id": {"$regex": f"^{re.escape(project_id)}:"}})
    await testing_db.projects.delete_one({"_id": project_id})
    await record_audit(
        current_user,
        "ADMIN_PROJECT_HARD_DELETED",
        project_id,
        payload.reason,
        {"project_key": project.get("key"), "deleted": deleted},
    )
    return APIResponse(
        data={"project_id": project_id, "deleted": deleted},
        message="Xóa dự án theo quy trình quản trị hoàn tất",
    )


@router.get("/bao-mat/truy-cap-khan-cap", response_model=APIResponse[Any])
async def list_break_glass_grants(
    active_only: bool = True, current_user: CurrentUser = Depends(get_current_user)
):
    testing_db = database.mongodb[os.environ.get("TESTING_DB_NAME", "veriq_testing")]
    query = (
        {"status": "ACTIVE", "expires_at": {"$gt": datetime.now(timezone.utc)}}
        if active_only
        else {}
    )
    values = await testing_db.break_glass_grants.find(query).sort("created_at", -1).to_list(1000)
    return APIResponse(data=values, message="Tải quyền truy cập khẩn cấp hoàn tất")


@router.post("/bao-mat/truy-cap-khan-cap", response_model=APIResponse[Any], status_code=201)
async def create_break_glass_grant(
    payload: BreakGlassCreateRequest, current_user: CurrentUser = Depends(get_current_user)
):
    testing_db = database.mongodb[os.environ.get("TESTING_DB_NAME", "veriq_testing")]
    if not await testing_db.projects.find_one({"_id": payload.project_id}, {"_id": 1}):
        raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
    await account_or_404(payload.user_id)
    grant = {
        "_id": f"break-glass-{uuid4().hex}",
        "project_id": payload.project_id,
        "user_id": payload.user_id,
        "permissions": sorted(set(payload.permissions)),
        "status": "ACTIVE",
        "reason": payload.reason,
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=payload.ttl_minutes),
    }
    await testing_db.break_glass_grants.insert_one(grant)
    await record_audit(
        current_user,
        "ADMIN_BREAK_GLASS_GRANTED",
        grant["_id"],
        payload.reason,
        {
            "project_id": payload.project_id,
            "user_id": payload.user_id,
            "permissions": grant["permissions"],
        },
    )
    return APIResponse(data=grant, message="Cấp quyền truy cập khẩn cấp hoàn tất", status=201)


@router.post("/bao-mat/truy-cap-khan-cap/{grant_id}/thu-hoi", response_model=APIResponse[Any])
async def revoke_break_glass_grant(
    grant_id: str, payload: ActionReason, current_user: CurrentUser = Depends(get_current_user)
):
    testing_db = database.mongodb[os.environ.get("TESTING_DB_NAME", "veriq_testing")]
    grant = await testing_db.break_glass_grants.find_one_and_update(
        {"_id": grant_id, "status": "ACTIVE"},
        {
            "$set": {
                "status": "REVOKED",
                "revoked_by": current_user.id,
                "revoked_at": datetime.now(timezone.utc),
                "revoke_reason": payload.reason,
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if not grant:
        raise HTTPException(status_code=409, detail="Quyền truy cập khẩn cấp không còn hoạt động")
    await record_audit(current_user, "ADMIN_BREAK_GLASS_REVOKED", grant_id, payload.reason)
    return APIResponse(data=grant, message="Thu hồi quyền truy cập khẩn cấp hoàn tất")


@router.get("/bao-mat/gioi-han-tan-suat", response_model=APIResponse[Any])
async def get_rate_limits(current_user: CurrentUser = Depends(get_current_user)):
    return await get_platform_config("rate_limits", current_user)


@router.patch("/bao-mat/gioi-han-tan-suat", response_model=APIResponse[Any])
async def update_rate_limits(
    payload: ConfigUpdate, current_user: CurrentUser = Depends(get_current_user)
):
    return await update_platform_config("rate_limits", payload, current_user)


@router.get("/bao-mat/danh-tinh-dich-vu", response_model=APIResponse[Any])
async def list_service_identities(current_user: CurrentUser = Depends(get_current_user)):
    values = (
        await database.mongodb[settings.AUTHENTICATION_DB_NAME]
        .service_identities.find({})
        .sort("name", 1)
        .to_list(500)
    )
    return APIResponse(
        data=[masked_reference(value) for value in values], message="Tải danh tính dịch vụ hoàn tất"
    )


@router.post("/bao-mat/danh-tinh-dich-vu", response_model=APIResponse[Any], status_code=201)
async def create_service_identity(
    payload: ServiceIdentityRequest, current_user: CurrentUser = Depends(get_current_user)
):
    timestamp = datetime.now(timezone.utc)
    value = {
        "_id": f"service-{uuid4().hex}",
        "name": payload.name,
        "secret_reference": payload.secret_reference,
        "scopes": sorted(set(payload.scopes)),
        "status": "ACTIVE",
        "revision": 1,
        "created_by": current_user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    await database.mongodb[settings.AUTHENTICATION_DB_NAME].service_identities.insert_one(value)
    await record_audit(
        current_user,
        "ADMIN_SERVICE_IDENTITY_CREATED",
        value["_id"],
        payload.reason,
        {"scopes": value["scopes"]},
    )
    return APIResponse(
        data=masked_reference(value), message="Tạo danh tính dịch vụ hoàn tất", status=201
    )


@router.post("/bao-mat/danh-tinh-dich-vu/{identity_id}/xoay-vong", response_model=APIResponse[Any])
async def rotate_service_identity(
    identity_id: str,
    payload: ServiceIdentityRotateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    value = await database.mongodb[
        settings.AUTHENTICATION_DB_NAME
    ].service_identities.find_one_and_update(
        {"_id": identity_id, "status": {"$ne": "REVOKED"}},
        {
            "$set": {
                "secret_reference": payload.secret_reference,
                "rotated_at": datetime.now(timezone.utc),
                "updated_by": current_user.id,
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not value:
        raise HTTPException(status_code=404, detail="Không tìm thấy danh tính dịch vụ")
    await record_audit(current_user, "ADMIN_SERVICE_IDENTITY_ROTATED", identity_id, payload.reason)
    return APIResponse(
        data=masked_reference(value), message="Luân chuyển tham chiếu danh tính dịch vụ hoàn tất"
    )


@router.post("/bao-mat/thu-hoi-khan-cap", response_model=APIResponse[Any])
async def emergency_revoke(
    payload: EmergencyRevokeRequest, current_user: CurrentUser = Depends(get_current_user)
):
    affected = 0
    auth_db = database.mongodb[settings.AUTHENTICATION_DB_NAME]
    if payload.scope == "USER":
        await account_or_404(payload.target_id or "")
        await IdentityRepository.revoke_all_sessions(payload.target_id or "")
        affected = 1
    elif payload.scope == "ALL_USERS":
        result = await auth_db.sessions.update_many(
            {"revoked_at": None}, {"$set": {"revoked_at": datetime.now(timezone.utc)}}
        )
        affected = result.modified_count
        async for key in redis.get_client().scan_iter(match="user_sessions:*"):
            await redis.delete(key)
    elif payload.scope == "SERVICE_IDENTITY":
        result = await auth_db.service_identities.update_one(
            {"_id": payload.target_id},
            {
                "$set": {
                    "status": "REVOKED",
                    "revoked_at": datetime.now(timezone.utc),
                    "revoked_by": current_user.id,
                }
            },
        )
        affected = result.modified_count
    else:
        result = await auth_db.service_identities.update_many(
            {"status": {"$ne": "REVOKED"}},
            {
                "$set": {
                    "status": "REVOKED",
                    "revoked_at": datetime.now(timezone.utc),
                    "revoked_by": current_user.id,
                }
            },
        )
        affected = result.modified_count
    await record_audit(
        current_user,
        "ADMIN_EMERGENCY_REVOKE",
        payload.target_id or "platform",
        payload.reason,
        {"scope": payload.scope, "affected": affected},
    )
    return APIResponse(
        data={"scope": payload.scope, "affected": affected}, message="Thu hồi khẩn cấp hoàn tất"
    )


@router.get("/bao-mat/nhat-ky", response_model=APIResponse[Any])
async def security_audit(
    action: str = Query(default="", max_length=100),
    actor: str = Query(default="", max_length=320),
    limit: int = Query(default=200, ge=1, le=2000),
    current_user: CurrentUser = Depends(get_current_user),
):
    query: dict[str, Any] = {}
    if action:
        query["action"] = {"$regex": action, "$options": "i"}
    if actor:
        query["actor_email"] = {"$regex": actor, "$options": "i"}
    values = (
        await database.mongodb[settings.AUTHENTICATION_DB_NAME]
        .audit_logs.find(query)
        .sort("timestamp", -1)
        .limit(limit)
        .to_list(limit)
    )
    return APIResponse(
        data=[{**value, "_id": str(value["_id"])} for value in values],
        message="Tải nhật ký bảo mật hoàn tất",
    )


@router.get("/bi-mat", response_model=APIResponse[Any])
async def list_secret_references(current_user: CurrentUser = Depends(get_current_user)):
    values = (
        await database.mongodb[settings.AUTHENTICATION_DB_NAME]
        .secret_references.find({})
        .sort("name", 1)
        .to_list(500)
    )
    return APIResponse(
        data=[masked_reference(value) for value in values], message="Tải tham chiếu bí mật hoàn tất"
    )


@router.post("/bi-mat", response_model=APIResponse[Any], status_code=201)
async def create_secret_reference(
    payload: SecretReferenceRequest, current_user: CurrentUser = Depends(get_current_user)
):
    timestamp = datetime.now(timezone.utc)
    value = {
        "_id": f"secret-ref-{uuid4().hex}",
        "name": payload.name,
        "provider": payload.provider,
        "reference": payload.reference,
        "revision": 1,
        "created_by": current_user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    await database.mongodb[settings.AUTHENTICATION_DB_NAME].secret_references.insert_one(value)
    await record_audit(
        current_user,
        "ADMIN_SECRET_REFERENCE_CREATED",
        value["_id"],
        payload.reason,
        {"provider": payload.provider},
    )
    return APIResponse(
        data=masked_reference(value), message="Tạo tham chiếu bí mật hoàn tất", status=201
    )


@router.post("/bi-mat/{reference_id}/xoay-vong", response_model=APIResponse[Any])
async def rotate_secret_reference(
    reference_id: str,
    payload: SecretReferenceRotateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    value = await database.mongodb[
        settings.AUTHENTICATION_DB_NAME
    ].secret_references.find_one_and_update(
        {"_id": reference_id},
        {
            "$set": {
                "reference": payload.reference,
                "rotated_at": datetime.now(timezone.utc),
                "updated_by": current_user.id,
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not value:
        raise HTTPException(status_code=404, detail="Không tìm thấy tham chiếu bí mật")
    await record_audit(current_user, "ADMIN_SECRET_REFERENCE_ROTATED", reference_id, payload.reason)
    return APIResponse(
        data=masked_reference(value), message="Luân chuyển tham chiếu bí mật hoàn tất"
    )


@router.delete("/bi-mat/{reference_id}", response_model=APIResponse[Any])
async def delete_secret_reference(
    reference_id: str, payload: ActionReason, current_user: CurrentUser = Depends(get_current_user)
):
    in_use = await database.mongodb[
        settings.AUTHENTICATION_DB_NAME
    ].service_identities.count_documents({"secret_reference": reference_id, "status": "ACTIVE"})
    if in_use:
        raise HTTPException(status_code=409, detail="Tham chiếu bí mật đang được sử dụng")
    result = await database.mongodb[settings.AUTHENTICATION_DB_NAME].secret_references.delete_one(
        {"_id": reference_id}
    )
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="Không tìm thấy tham chiếu bí mật")
    await record_audit(current_user, "ADMIN_SECRET_REFERENCE_DELETED", reference_id, payload.reason)
    return APIResponse(
        data={"reference_id": reference_id, "deleted": True},
        message="Xóa tham chiếu bí mật hoàn tất",
    )


@router.post("/tich-hop/smtp/kiem-tra", response_model=APIResponse[Any])
async def test_smtp(
    payload: SmtpTestRequest, current_user: CurrentUser = Depends(get_current_user)
):
    try:
        await EmailService.send_platform_test_email(str(payload.recipient))
    except Exception as error:
        await record_audit(
            current_user, "ADMIN_SMTP_TEST_FAILED", str(payload.recipient), payload.reason
        )
        raise HTTPException(status_code=503, detail="Không thể gửi thư kiểm tra") from error
    await record_audit(current_user, "ADMIN_SMTP_TESTED", str(payload.recipient), payload.reason)
    return APIResponse(
        data={"recipient": payload.recipient, "delivered": True},
        message="Gửi thư kiểm tra hoàn tất",
    )


@router.get("/van-hanh/hang-doi", response_model=APIResponse[Any])
async def queue_overview(current_user: CurrentUser = Depends(get_current_user)):
    worker_db = database.mongodb[os.environ.get("WORKER_DB_NAME", "veriq_worker")]
    rows = await worker_db.worker_jobs.aggregate(
        [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    ).to_list(100)
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get("http://worker:8000/san-sang")
            worker = response.json()
    except (httpx.HTTPError, ValueError):
        worker = {"status": "unavailable", "checks": {"consumers": "unavailable"}}
    return APIResponse(
        data={
            "jobs_by_status": {row["_id"]: row["count"] for row in rows},
            "consumer_status": worker.get("checks", {}).get("consumers"),
            "worker_status": worker.get("status"),
        },
        message="Tải trạng thái hàng đợi hoàn tất",
    )


@router.post("/van-hanh/dlq/{job_id}/dua-lai-hang-doi", response_model=APIResponse[Any], status_code=202)
async def requeue_dead_letter_job(
    job_id: str, payload: ActionReason, current_user: CurrentUser = Depends(get_current_user)
):
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"http://worker:8000/xu-ly-nen/noi-bo/tac-vu/{job_id}/thu-lai",
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
            response.raise_for_status()
            result = response.json()
    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=error.response.status_code,
            detail="Không thể đưa tác vụ lỗi trở lại hàng đợi",
        ) from error
    except httpx.HTTPError as error:
        raise HTTPException(status_code=503, detail="Dịch vụ tác vụ nền chưa sẵn sàng") from error
    await record_audit(current_user, "ADMIN_DLQ_JOB_REQUEUED", job_id, payload.reason)
    return APIResponse(data=result, message="Đưa tác vụ lỗi trở lại hàng đợi hoàn tất", status=202)


@router.get("/van-hanh/rag", response_model=APIResponse[Any])
async def rag_operations(current_user: CurrentUser = Depends(get_current_user)):
    testing_db = database.mongodb[os.environ.get("TESTING_DB_NAME", "veriq_testing")]
    values = {}
    for collection_name in ["requirement_documents", "requirement_versions", "test_case_versions"]:
        rows = (
            await testing_db[collection_name]
            .aggregate([{"$group": {"_id": "$index_status", "count": {"$sum": 1}}}])
            .to_list(100)
        )
        values[collection_name] = {(row["_id"] or "UNKNOWN"): row["count"] for row in rows}
    return APIResponse(data=values, message="Tải trạng thái lập chỉ mục tri thức hoàn tất")


@router.post("/van-hanh/rag/lap-chi-muc-lai", response_model=APIResponse[Any], status_code=202)
async def request_rag_reindex(
    payload: RagReindexRequest, current_user: CurrentUser = Depends(get_current_user)
):
    testing_db = database.mongodb[os.environ.get("TESTING_DB_NAME", "veriq_testing")]
    if not await testing_db.projects.find_one({"_id": payload.project_id}, {"_id": 1}):
        raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
    artifact_ids = list(dict.fromkeys(payload.artifact_version_ids))
    if not artifact_ids:
        requirement_ids = await testing_db.requirement_versions.distinct(
            "_id", {"project_id": payload.project_id, "status": "BASELINED"}
        )
        test_case_ids = await testing_db.test_case_versions.distinct(
            "_id", {"project_id": payload.project_id, "status": "APPROVED"}
        )
        artifact_ids = requirement_ids + test_case_ids
    accepted = []
    async with httpx.AsyncClient(timeout=15) as client:
        for artifact_id in artifact_ids:
            request_body = {
                "event": "knowledge.index.requested",
                "project_id": payload.project_id,
                "artifact_version_id": artifact_id,
                "model_version": "admin-reindex-v1",
                "requester_id": current_user.id,
                "requester_email": current_user.email,
                "payload": {},
            }
            try:
                response = await client.post(
                    "http://worker:8000/xu-ly-nen/noi-bo/kiem-thu/tac-vu",
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                    json=request_body,
                )
                response.raise_for_status()
                accepted.append(response.json())
            except httpx.HTTPError as error:
                raise HTTPException(
                    status_code=503, detail="Không thể gửi yêu cầu lập chỉ mục"
                ) from error
    await record_audit(
        current_user,
        "ADMIN_RAG_REINDEX_REQUESTED",
        payload.project_id,
        payload.reason,
        {"artifact_count": len(accepted)},
    )
    return APIResponse(
        data={"project_id": payload.project_id, "jobs": accepted},
        message="Tiếp nhận yêu cầu lập chỉ mục lại hoàn tất",
        status=202,
    )


@router.get("/van-hanh/bo-nho-dem", response_model=APIResponse[Any])
async def inspect_safe_caches(current_user: CurrentUser = Depends(get_current_user)):
    patterns = {
        "RATE_LIMITS": "rate_limit:*",
        "PASSKEY_CHALLENGES": "passkey_challenge:*",
        "PROJECT_METADATA": "project_metadata:*",
    }
    counts = {}
    client = redis.get_client()
    for name, pattern in patterns.items():
        counts[name] = sum([1 async for _ in client.scan_iter(match=pattern)])
    return APIResponse(data=counts, message="Tải trạng thái bộ đệm an toàn hoàn tất")


@router.post("/van-hanh/bo-nho-dem/don-sach", response_model=APIResponse[Any])
async def clear_safe_caches(
    payload: CacheClearRequest, current_user: CurrentUser = Depends(get_current_user)
):
    patterns = {
        "RATE_LIMITS": ["rate_limit:*"],
        "PASSKEY_CHALLENGES": ["passkey_challenge:*"],
        "PROJECT_METADATA": ["project_metadata:*"],
        "SAFE_ALL": ["rate_limit:*", "passkey_challenge:*", "project_metadata:*"],
    }
    keys = []
    client = redis.get_client()
    for pattern in patterns[payload.scope]:
        keys.extend([key async for key in client.scan_iter(match=pattern)])
    if keys:
        await client.delete(*keys)
    await record_audit(
        current_user,
        "ADMIN_SAFE_CACHE_CLEARED",
        payload.scope,
        payload.reason,
        {"deleted": len(keys)},
    )
    return APIResponse(
        data={"scope": payload.scope, "deleted": len(keys)}, message="Xóa bộ đệm an toàn hoàn tất"
    )


def attachment_size(value):
    if isinstance(value, dict):
        return sum(
            int(item)
            if key in {"size", "size_bytes", "bytes", "byte_size"}
            and isinstance(item, (int, float))
            else attachment_size(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return sum(attachment_size(item) for item in value)
    return 0


@router.get("/van-hanh/dung-luong-luu-tru", response_model=APIResponse[Any])
async def storage_usage(current_user: CurrentUser = Depends(get_current_user)):
    testing_db = database.mongodb[os.environ.get("TESTING_DB_NAME", "veriq_testing")]
    projects = await testing_db.projects.find({}, {"key": 1, "name": 1}).to_list(10000)
    sources = [
        ("requirement_documents", "raw_source"),
        ("test_case_drafts", "attachments"),
        ("test_case_versions", "attachments"),
        ("test_results", "attachments"),
        ("defects", "attachments"),
    ]
    values = []
    for project in projects:
        total = 0
        files = 0
        for collection_name, field in sources:
            documents = (
                await testing_db[collection_name]
                .find({"project_id": project["_id"]}, {field: 1})
                .to_list(100000)
            )
            for document in documents:
                value = document.get(field)
                total += attachment_size(value)
                files += len(value) if isinstance(value, list) else int(bool(value))
        values.append(
            {
                "project_id": project["_id"],
                "project_key": project.get("key"),
                "project_name": project.get("name"),
                "bytes": total,
                "files": files,
            }
        )
    values.sort(key=lambda item: item["bytes"], reverse=True)
    return APIResponse(
        data={
            "projects": values,
            "total_bytes": sum(item["bytes"] for item in values),
            "total_files": sum(item["files"] for item in values),
        },
        message="Tải dung lượng lưu trữ hoàn tất",
    )


@router.get("/van-hanh/phien-ban-van-hanh", response_model=APIResponse[Any])
async def runtime_versions(current_user: CurrentUser = Depends(get_current_user)):
    targets = {
        "authentication": "http://authentication:8000/san-sang",
        "testing": "http://testing:8000/san-sang",
        "worker": "http://worker:8000/san-sang",
        "ai": "http://ai:8000/suc-khoe",
        "cloud": "http://cloud:8000/san-sang",
    }
    results = []
    async with httpx.AsyncClient(timeout=5) as client:
        for name, url in targets.items():
            try:
                response = await client.get(url)
                results.append(
                    {
                        "service": name,
                        "healthy": response.status_code < 400,
                        "runtime_version": os.environ.get("VERSION", "unknown"),
                        "details": response.json(),
                    }
                )
            except (httpx.HTTPError, ValueError):
                results.append(
                    {
                        "service": name,
                        "healthy": False,
                        "runtime_version": "unknown",
                        "details": {"status": "unavailable"},
                    }
                )
    return APIResponse(
        data={
            "services": results,
            "schema_version": "v4.3",
            "platform_version": os.environ.get("VERSION", "unknown"),
        },
        message="Tải phiên bản vận hành hoàn tất",
    )


@router.get("/cau-hinh/bao-tri", response_model=APIResponse[Any])
async def get_maintenance_mode(current_user: CurrentUser = Depends(get_current_user)):
    return await get_platform_config("maintenance", current_user)


@router.patch("/cau-hinh/bao-tri", response_model=APIResponse[Any])
async def update_maintenance_mode(
    payload: MaintenanceModeRequest, current_user: CurrentUser = Depends(get_current_user)
):
    return await update_platform_config(
        "maintenance",
        ConfigUpdate(
            values={"enabled": payload.enabled, "banner": payload.banner}, reason=payload.reason
        ),
        current_user,
    )


def config_routes(config_type: str):
    async def get_value(current_user: CurrentUser = Depends(get_current_user)):
        return await get_platform_config(config_type, current_user)

    async def update_value(
        payload: ConfigUpdate, current_user: CurrentUser = Depends(get_current_user)
    ):
        return await update_platform_config(config_type, payload, current_user)

    return get_value, update_value


for route_path, config_type in [
    ("/cau-hinh/co-tinh-nang", "feature_flags"),
    ("/cau-hinh/dia-phuong-hoa", "localization"),
    ("/cau-hinh/luu-giu", "retention"),
    ("/cau-hinh/han-muc-mac-dinh", "default_quotas"),
    ("/cau-hinh/nhap-xuat", "import_export"),
    ("/bao-mat/chinh-sach-truy-cap-khan-cap", "break_glass_policy"),
    ("/ai/gioi-han", "ai_limits"),
    ("/ai/truy-xuat", "ai_retrieval"),
]:
    get_handler, update_handler = config_routes(config_type)
    router.add_api_route(
        route_path,
        get_handler,
        methods=["GET"],
        response_model=APIResponse[Any],
        name=f"get_{config_type}",
    )
    router.add_api_route(
        route_path,
        update_handler,
        methods=["PATCH"],
        response_model=APIResponse[Any],
        name=f"update_{config_type}",
    )
