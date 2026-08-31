import asyncio
import csv
import io
import os
import re
import secrets
from datetime import datetime, timezone
from typing import Any

import httpx
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field, model_validator
from pymongo import ReturnDocument

from src.api.internal import account_view
from src.core.dependency import CurrentUser, Role, SystemRole, get_current_user
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.response import APIResponse
from src.repositories.identity import IdentityRepository
from src.schemas.identity import UserCreate
from src.services.session import SessionService


class AccountUpdate(BaseModel):
    role: Role | None = None
    system_role: SystemRole | None = None
    is_active: bool | None = None
    reason: str = Field(min_length=3, max_length=1000)

    @model_validator(mode="after")
    def validate_change(self):
        if self.role is None and self.system_role is None and self.is_active is None:
            raise ValueError("Cần cung cấp thay đổi vai trò hoặc trạng thái")
        return self


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    slug: str | None = Field(default=None, min_length=2, max_length=100)
    reason: str = Field(min_length=3, max_length=1000)


class UserCreateRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)
    slug: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    reason: str = Field(min_length=3, max_length=1000)


class ActionReason(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)


class SystemRoleUpdate(BaseModel):
    system_role: SystemRole
    reason: str = Field(min_length=3, max_length=1000)


class ProjectPolicyUpdate(BaseModel):
    project_creation_policy: str = Field(pattern="^(AUTHENTICATED|ADMIN_ONLY)$")
    reason: str = Field(min_length=3, max_length=1000)


class ProviderUpdate(BaseModel):
    enabled: bool | None = None
    model: str | None = Field(default=None, min_length=1, max_length=200)
    timeout_seconds: int | None = Field(default=None, ge=1, le=3600)
    max_output_tokens: int | None = Field(default=None, ge=128, le=131072)
    secret_reference: str | None = Field(default=None, min_length=1, max_length=300)
    reason: str = Field(min_length=3, max_length=1000)


class ConfigUpdate(BaseModel):
    values: dict[str, Any]
    reason: str = Field(min_length=3, max_length=1000)


class ModelRegistryEntry(BaseModel):
    provider_id: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=200)
    version: str | None = Field(default=None, max_length=100)
    enabled: bool = True
    capabilities: list[str] = Field(default_factory=list, max_length=30)
    reason: str = Field(min_length=3, max_length=1000)


class ProjectStatusUpdate(BaseModel):
    status: str = Field(pattern="^(ACTIVE|SUSPENDED)$")
    reason: str = Field(min_length=3, max_length=1000)


class ProjectQuotaUpdate(BaseModel):
    storage_bytes: int | None = Field(default=None, ge=0)
    ai_requests_per_day: int | None = Field(default=None, ge=0)
    concurrent_jobs: int | None = Field(default=None, ge=0, le=10000)
    reason: str = Field(min_length=3, max_length=1000)


async def account_or_404(user_id: str):
    account = await database.mongodb[
        settings.AUTHENTICATION_DB_NAME
    ].auth_credentials.find_one({"_id": user_id})
    if not account:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
    return account


async def protect_last_admin(account: dict, desired_role=None, desired_active=None):
    current_role = account.get(
        "system_role", "ADMIN" if account.get("role") == "admin" else "USER"
    )
    removing_admin = current_role == "ADMIN" and (
        desired_role == "USER" or desired_active is False
    )
    if not removing_admin:
        return
    active_admins = await database.mongodb[
        settings.AUTHENTICATION_DB_NAME
    ].auth_credentials.count_documents(
        {
            "is_active": {"$ne": False},
            "$or": [{"system_role": "ADMIN"}, {"role": "admin"}],
        }
    )
    if active_admins <= 1:
        raise HTTPException(
            status_code=422,
            detail="Không thể vô hiệu hóa quản trị viên cuối cùng",
        )


async def record_audit(
    current_user: CurrentUser,
    action: str,
    user_id: str,
    reason: str,
    details=None,
):
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


router = APIRouter(dependencies=[Depends(require_system_admin)])


@router.post("/quan-tri/tai-khoan", response_model=APIResponse[Any], status_code=201)
async def create_account(
    payload: UserCreateRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
):
    generated_password = secrets.token_urlsafe(48)
    user = await SessionService.register_user(
        UserCreate(
            email=payload.email,
            full_name=payload.full_name,
            slug=payload.slug,
            password=generated_password,
            agreed_to_terms=True,
        ),
        request.client.host if request.client else "admin",
    )
    await SessionService.forgot_password(
        str(payload.email),
        request.client.host if request.client else "admin",
    )
    await record_audit(
        current_user,
        "ADMIN_USER_CREATED",
        user["id"],
        payload.reason,
        {"invite_flow": "PASSWORD_RESET"},
    )
    account = await account_or_404(user["id"])
    return APIResponse(
        data=account_view(account),
        message="Tạo tài khoản và khởi tạo lời mời đặt mật khẩu hoàn tất",
    )


@router.get("/quan-tri/tai-khoan", response_model=APIResponse[Any])
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


@router.patch("/quan-tri/tai-khoan/{user_id}", response_model=APIResponse[Any])
async def update_account(
    user_id: str, payload: AccountUpdate, current_user: CurrentUser = Depends(get_current_user)
):
    if user_id == current_user.id and (
        payload.is_active is False
        or payload.role not in {None, Role.ADMIN}
        or payload.system_role not in {None, SystemRole.ADMIN}
    ):
        raise HTTPException(
            status_code=422, detail="Không thể tự khóa hoặc hạ quyền tài khoản quản trị hiện tại"
        )
    account_before = await account_or_404(user_id)
    desired_role = payload.system_role.value if payload.system_role is not None else None
    await protect_last_admin(account_before, desired_role, payload.is_active)
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


@router.get("/quan-tri/tai-khoan/{user_id}", response_model=APIResponse[Any])
async def account_detail(
    user_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    account = await account_or_404(user_id)
    session_count = await database.mongodb[
        settings.AUTHENTICATION_DB_NAME
    ].sessions.count_documents({"user_id": user_id, "revoked_at": None})
    passkey_count = len(account.get("passkeys", []))
    return APIResponse(
        data={
            **account_view(account),
            "account_status": account.get(
                "account_status", "ACTIVE" if account.get("is_active", True) else "DISABLED"
            ),
            "active_session_count": session_count,
            "passkey_count": passkey_count,
            "is_verified": account.get("is_verified", False),
            "last_password_change": account.get("last_password_change"),
        },
        message="Tải chi tiết tài khoản hoàn tất",
    )


@router.patch("/quan-tri/tai-khoan/{user_id}/ho-so", response_model=APIResponse[Any])
async def update_account_profile(
    user_id: str,
    payload: ProfileUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    await account_or_404(user_id)
    changes = {
        key: value
        for key, value in payload.model_dump(exclude={"reason"}).items()
        if value is not None
    }
    if not changes:
        raise HTTPException(status_code=422, detail="Không có dữ liệu cần cập nhật")
    changes["updated_at"] = datetime.now(timezone.utc)
    account = await database.mongodb[
        settings.AUTHENTICATION_DB_NAME
    ].auth_credentials.find_one_and_update(
        {"_id": user_id}, {"$set": changes}, return_document=ReturnDocument.AFTER
    )
    await record_audit(
        current_user,
        "ADMIN_USER_PROFILE_UPDATED",
        user_id,
        payload.reason,
        changes,
    )
    return APIResponse(data=account_view(account), message="Cập nhật hồ sơ tài khoản hoàn tất")


async def change_account_status(
    user_id: str,
    desired_status: str,
    payload: ActionReason,
    current_user: CurrentUser,
):
    account = await account_or_404(user_id)
    active = desired_status == "ACTIVE"
    await protect_last_admin(account, desired_active=active)
    if user_id == current_user.id and not active:
        raise HTTPException(status_code=422, detail="Không thể tự vô hiệu hóa tài khoản hiện tại")
    updated_at = datetime.now(timezone.utc)
    account = await database.mongodb[
        settings.AUTHENTICATION_DB_NAME
    ].auth_credentials.find_one_and_update(
        {"_id": user_id},
        {
            "$set": {
                "is_active": active,
                "account_status": desired_status,
                "updated_at": updated_at,
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if not active:
        await IdentityRepository.revoke_all_sessions(user_id)
    await record_audit(
        current_user,
        f"ADMIN_USER_{desired_status}",
        user_id,
        payload.reason,
    )
    return APIResponse(data=account_view(account), message="Cập nhật trạng thái tài khoản hoàn tất")


@router.post("/quan-tri/tai-khoan/{user_id}/kich-hoat", response_model=APIResponse[Any])
async def enable_account(
    user_id: str,
    payload: ActionReason,
    current_user: CurrentUser = Depends(get_current_user),
):
    return await change_account_status(user_id, "ACTIVE", payload, current_user)


@router.post("/quan-tri/tai-khoan/{user_id}/vo-hieu-hoa", response_model=APIResponse[Any])
async def disable_account(
    user_id: str,
    payload: ActionReason,
    current_user: CurrentUser = Depends(get_current_user),
):
    return await change_account_status(user_id, "DISABLED", payload, current_user)


@router.post("/quan-tri/tai-khoan/{user_id}/khoa", response_model=APIResponse[Any])
async def lock_account(
    user_id: str,
    payload: ActionReason,
    current_user: CurrentUser = Depends(get_current_user),
):
    return await change_account_status(user_id, "LOCKED", payload, current_user)


@router.post("/quan-tri/tai-khoan/{user_id}/mo-khoa", response_model=APIResponse[Any])
async def unlock_account(
    user_id: str,
    payload: ActionReason,
    current_user: CurrentUser = Depends(get_current_user),
):
    return await change_account_status(user_id, "ACTIVE", payload, current_user)


@router.post("/quan-tri/tai-khoan/{user_id}/bat-buoc-doi-mat-khau", response_model=APIResponse[Any])
async def force_password_reset(
    user_id: str,
    payload: ActionReason,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
):
    account = await account_or_404(user_id)
    result = await SessionService.forgot_password(
        account["email"], request.client.host if request.client else "unknown"
    )
    await IdentityRepository.revoke_all_sessions(user_id)
    await record_audit(current_user, "ADMIN_FORCE_PASSWORD_RESET", user_id, payload.reason)
    return APIResponse(data=result, message="Khởi tạo quy trình đặt lại mật khẩu hoàn tất")


@router.get("/quan-tri/tai-khoan/{user_id}/phien", response_model=APIResponse[Any])
async def list_user_sessions(
    user_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    await account_or_404(user_id)
    sessions = (
        await database.mongodb[settings.AUTHENTICATION_DB_NAME]
        .sessions.find({"user_id": user_id}, {"refresh_token_hash": 0})
        .sort("created_at", -1)
        .to_list(500)
    )
    await record_audit(current_user, "ADMIN_USER_SESSIONS_VIEWED", user_id, "security review")
    return APIResponse(data=sessions, message="Tải danh sách phiên đăng nhập hoàn tất")


@router.delete("/quan-tri/tai-khoan/{user_id}/phien/{session_id}", response_model=APIResponse[Any])
async def revoke_user_session(
    user_id: str,
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    await account_or_404(user_id)
    await IdentityRepository.revoke_session(user_id, session_id)
    await record_audit(
        current_user,
        "ADMIN_USER_SESSION_REVOKED",
        user_id,
        "security action",
        {"session_id": session_id},
    )
    return APIResponse(
        data={"revoked": True, "session_id": session_id},
        message="Thu hồi phiên hoàn tất",
    )


@router.delete("/quan-tri/tai-khoan/{user_id}/phien", response_model=APIResponse[Any])
async def revoke_all_user_sessions(
    user_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    await account_or_404(user_id)
    await IdentityRepository.revoke_all_sessions(user_id)
    await record_audit(
        current_user,
        "ADMIN_USER_SESSIONS_REVOKED",
        user_id,
        "security action",
    )
    return APIResponse(data={"revoked": True}, message="Thu hồi toàn bộ phiên hoàn tất")


@router.delete("/quan-tri/tai-khoan/{user_id}/khoa-bao-mat", response_model=APIResponse[Any])
async def reset_user_passkeys(
    user_id: str,
    payload: ActionReason,
    current_user: CurrentUser = Depends(get_current_user),
):
    await account_or_404(user_id)
    await database.mongodb[settings.AUTHENTICATION_DB_NAME].auth_credentials.update_one(
        {"_id": user_id}, {"$set": {"passkeys": [], "updated_at": datetime.now(timezone.utc)}}
    )
    await IdentityRepository.revoke_all_sessions(user_id)
    await record_audit(current_user, "ADMIN_USER_PASSKEYS_RESET", user_id, payload.reason)
    return APIResponse(data={"reset": True}, message="Đặt lại passkey hoàn tất")


@router.patch("/quan-tri/tai-khoan/{user_id}/vai-tro-he-thong", response_model=APIResponse[Any])
async def update_system_role(
    user_id: str,
    payload: SystemRoleUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    account = await account_or_404(user_id)
    await protect_last_admin(account, desired_role=payload.system_role.value)
    if user_id == current_user.id and payload.system_role != SystemRole.ADMIN:
        raise HTTPException(status_code=422, detail="Không thể tự hạ quyền quản trị hiện tại")
    account = await database.mongodb[
        settings.AUTHENTICATION_DB_NAME
    ].auth_credentials.find_one_and_update(
        {"_id": user_id},
        {
            "$set": {
                "system_role": payload.system_role.value,
                "role": "admin" if payload.system_role == SystemRole.ADMIN else "reader",
                "updated_at": datetime.now(timezone.utc),
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    await IdentityRepository.revoke_all_sessions(user_id)
    await record_audit(
        current_user,
        "ADMIN_SYSTEM_ROLE_UPDATED",
        user_id,
        payload.reason,
        {"system_role": payload.system_role.value},
    )
    return APIResponse(data=account_view(account), message="Cập nhật vai trò hệ thống hoàn tất")


@router.get("/quan-tri/tai-khoan/{user_id}/vai-tro-du-an", response_model=APIResponse[Any])
async def list_user_memberships(
    user_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    await account_or_404(user_id)
    testing_db_name = os.environ.get("TESTING_DB_NAME", "veriq_testing")
    memberships = (
        await database.mongodb[testing_db_name]
        .project_members.find(
            {"user_id": user_id},
            {"project_id": 1, "project_role": 1, "status": 1, "membership_revision": 1},
        )
        .to_list(5000)
    )
    await record_audit(current_user, "ADMIN_USER_MEMBERSHIPS_VIEWED", user_id, "support metadata")
    return APIResponse(data=memberships, message="Tải siêu dữ liệu thành viên dự án hoàn tất")


@router.get("/quan-tri/tai-khoan/{user_id}/nhat-ky", response_model=APIResponse[Any])
async def list_user_audit(
    user_id: str,
    limit: int = Query(default=200, ge=1, le=1000),
    current_user: CurrentUser = Depends(get_current_user),
):
    account = await account_or_404(user_id)
    events = (
        await database.mongodb[settings.AUTHENTICATION_DB_NAME]
        .audit_logs.find(
            {"$or": [{"target_user_id": user_id}, {"actor_email": account.get("email")}]}
        )
        .sort("timestamp", -1)
        .limit(limit)
        .to_list(limit)
    )
    return APIResponse(
        data=[{**event, "_id": str(event["_id"])} for event in events],
        message="Tải nhật ký bảo mật tài khoản hoàn tất",
    )


@router.get("/quan-tri/du-an", response_model=APIResponse[Any])
async def list_project_metadata(
    search: str = Query(default="", max_length=200),
    status: str = Query(default="", max_length=30),
    limit: int = Query(default=200, ge=1, le=1000),
    current_user: CurrentUser = Depends(get_current_user),
):
    testing_db = database.mongodb[os.environ.get("TESTING_DB_NAME", "veriq_testing")]
    query: dict[str, Any] = {}
    if status:
        query["status"] = status
    if search:
        pattern = re.escape(search.strip())
        query["$or"] = [
            {"key": {"$regex": pattern, "$options": "i"}},
            {"name": {"$regex": pattern, "$options": "i"}},
        ]
    projects = await testing_db.projects.find(
        query,
        {
            "key": 1,
            "name": 1,
            "status": 1,
            "administrative_status": 1,
            "project_type": 1,
            "quota": 1,
            "created_by": 1,
            "created_at": 1,
            "updated_at": 1,
        },
    ).sort("updated_at", -1).limit(limit).to_list(limit)
    project_ids = [project["_id"] for project in projects]
    member_counts = await testing_db.project_members.aggregate(
        [
            {"$match": {"project_id": {"$in": project_ids}}},
            {"$group": {"_id": "$project_id", "count": {"$sum": 1}}},
        ]
    ).to_list(limit)
    count_by_project = {item["_id"]: item["count"] for item in member_counts}
    data = [
        {**project, "member_count": count_by_project.get(project["_id"], 0)}
        for project in projects
    ]
    await record_audit(current_user, "ADMIN_PROJECT_METADATA_VIEWED", "platform", "operations")
    return APIResponse(data=data, message="Tải siêu dữ liệu dự án hoàn tất")


@router.get("/quan-tri/du-an/{project_id}", response_model=APIResponse[Any])
async def project_metadata_detail(
    project_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    testing_db = database.mongodb[os.environ.get("TESTING_DB_NAME", "veriq_testing")]
    project = await testing_db.projects.find_one(
        {"_id": project_id},
        {"key": 1, "name": 1, "status": 1, "project_type": 1, "created_by": 1, "created_at": 1, "updated_at": 1, "revision": 1, "quota": 1},
    )
    if not project:
        raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
    project["member_count"] = await testing_db.project_members.count_documents({"project_id": project_id})
    project["active_member_count"] = await testing_db.project_members.count_documents({"project_id": project_id, "status": "ACTIVE"})
    project["job_count"] = await database.mongodb[os.environ.get("WORKER_DB_NAME", "veriq_worker")].worker_jobs.count_documents({"project_id": project_id})
    await record_audit(current_user, "ADMIN_PROJECT_METADATA_VIEWED", project_id, "support metadata")
    return APIResponse(data=project, message="Tải siêu dữ liệu dự án hoàn tất")


@router.patch("/quan-tri/du-an/{project_id}/trang-thai", response_model=APIResponse[Any])
async def update_project_status(
    project_id: str,
    payload: ProjectStatusUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    testing_db = database.mongodb[os.environ.get("TESTING_DB_NAME", "veriq_testing")]
    timestamp = datetime.now(timezone.utc)
    project = await testing_db.projects.find_one_and_update(
        {"_id": project_id},
        {"$set": {"administrative_status": payload.status, "administrative_reason": payload.reason, "administrative_updated_by": current_user.id, "administrative_updated_at": timestamp, "updated_at": timestamp}, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
    await record_audit(current_user, "ADMIN_PROJECT_STATUS_UPDATED", project_id, payload.reason, {"status": payload.status})
    return APIResponse(data=project, message="Cập nhật trạng thái quản trị dự án hoàn tất")


@router.patch("/quan-tri/du-an/{project_id}/han-muc", response_model=APIResponse[Any])
async def update_project_quota(
    project_id: str,
    payload: ProjectQuotaUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    quota = payload.model_dump(exclude={"reason"}, exclude_none=True)
    if not quota:
        raise HTTPException(status_code=422, detail="Không có hạn mức cần cập nhật")
    testing_db = database.mongodb[os.environ.get("TESTING_DB_NAME", "veriq_testing")]
    project = await testing_db.projects.find_one_and_update(
        {"_id": project_id},
        {"$set": {"quota": quota, "quota_updated_by": current_user.id, "quota_updated_at": datetime.now(timezone.utc)}, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
    await record_audit(current_user, "ADMIN_PROJECT_QUOTA_UPDATED", project_id, payload.reason, quota)
    return APIResponse(data={"project_id": project_id, "quota": quota}, message="Cập nhật hạn mức dự án hoàn tất")


@router.get("/quan-tri/nen-tang/chinh-sach-du-an", response_model=APIResponse[Any])
async def get_project_policy(
    current_user: CurrentUser = Depends(get_current_user),
):
    config = await database.mongodb[settings.AUTHENTICATION_DB_NAME].system_configs.find_one(
        {"type": "project_creation"}
    )
    return APIResponse(
        data={
            "project_creation_policy": (config or {}).get(
                "project_creation_policy", "AUTHENTICATED"
            ),
            "updated_at": (config or {}).get("updated_at"),
        },
        message="Tải chính sách tạo dự án hoàn tất",
    )


@router.patch("/quan-tri/nen-tang/chinh-sach-du-an", response_model=APIResponse[Any])
async def update_project_policy(
    payload: ProjectPolicyUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    timestamp = datetime.now(timezone.utc)
    await database.mongodb[settings.AUTHENTICATION_DB_NAME].system_configs.update_one(
        {"type": "project_creation"},
        {
            "$set": {
                "project_creation_policy": payload.project_creation_policy,
                "updated_at": timestamp,
                "updated_by": current_user.id,
            },
            "$setOnInsert": {"type": "project_creation", "created_at": timestamp},
        },
        upsert=True,
    )
    await record_audit(
        current_user,
        "ADMIN_PROJECT_POLICY_UPDATED",
        "platform",
        payload.reason,
        {"project_creation_policy": payload.project_creation_policy},
    )
    return APIResponse(
        data={"project_creation_policy": payload.project_creation_policy},
        message="Cập nhật chính sách tạo dự án hoàn tất",
    )


def provider_view(provider: dict):
    return {
        "_id": provider["_id"],
        "enabled": provider.get("enabled", True),
        "model": provider.get("model", ""),
        "timeout_seconds": provider.get("timeout_seconds"),
        "max_output_tokens": provider.get("max_output_tokens"),
        "secret_reference": "Đã cấu hình" if provider.get("secret_reference") else None,
        "updated_at": provider.get("updated_at"),
        "requires_restart": provider.get("requires_restart", False),
    }


@router.get("/quan-tri/ai/nha-cung-cap", response_model=APIResponse[Any])
async def list_ai_providers(
    current_user: CurrentUser = Depends(get_current_user),
):
    collection = database.mongodb[settings.AUTHENTICATION_DB_NAME].ai_providers
    providers = await collection.find({}).sort("_id", 1).to_list(100)
    if not providers:
        providers = [
            {
                "_id": os.environ.get("PRIMARY_MODEL_STYLE", "ollama"),
                "enabled": True,
                "model": os.environ.get("LLM_MODEL", ""),
                "timeout_seconds": int(os.environ.get("MODEL_TIMEOUT_SECONDS", "900")),
                "max_output_tokens": int(os.environ.get("AGENT_DEFAULT_MAX_OUTPUT_TOKENS", "4096")),
                "secret_reference": bool(os.environ.get("PRIMARY_MODEL_API_TOKEN")),
                "requires_restart": False,
            }
        ]
    return APIResponse(
        data=[provider_view(provider) for provider in providers],
        message="Tải cấu hình nhà cung cấp AI hoàn tất",
    )


@router.patch("/quan-tri/ai/nha-cung-cap/{provider_id}", response_model=APIResponse[Any])
async def update_ai_provider(
    provider_id: str,
    payload: ProviderUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    changes = {
        key: value
        for key, value in payload.model_dump(exclude={"reason"}).items()
        if value is not None
    }
    if not changes:
        raise HTTPException(status_code=422, detail="Không có cấu hình cần cập nhật")
    timestamp = datetime.now(timezone.utc)
    changes.update(
        {"updated_at": timestamp, "updated_by": current_user.id, "requires_restart": True}
    )
    provider = await database.mongodb[
        settings.AUTHENTICATION_DB_NAME
    ].ai_providers.find_one_and_update(
        {"_id": provider_id},
        {"$set": changes, "$setOnInsert": {"created_at": timestamp}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    await record_audit(current_user, "ADMIN_AI_PROVIDER_UPDATED", provider_id, payload.reason)
    return APIResponse(data=provider_view(provider), message="Cập nhật cấu hình AI hoàn tất")


@router.post("/quan-tri/ai/nha-cung-cap/{provider_id}/kiem-tra", response_model=APIResponse[Any])
async def test_ai_provider(
    provider_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    ai_url = os.environ.get("AI_INTERNAL_URL", "http://ai:8000").rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"{ai_url}/san-sang")
            response.raise_for_status()
            health = response.json()
    except httpx.HTTPError as error:
        await record_audit(current_user, "ADMIN_AI_PROVIDER_TEST_FAILED", provider_id, "health test")
        raise HTTPException(status_code=503, detail="Nhà cung cấp AI chưa sẵn sàng") from error
    await record_audit(current_user, "ADMIN_AI_PROVIDER_TESTED", provider_id, "health test")
    return APIResponse(
        data={"provider_id": provider_id, "healthy": True, "service": health},
        message="Kiểm tra kết nối AI hoàn tất",
    )


@router.get("/quan-tri/van-hanh/tac-vu", response_model=APIResponse[Any])
async def list_operations_jobs(
    status: str = Query(default="", max_length=30),
    kind: str = Query(default="", max_length=100),
    limit: int = Query(default=200, ge=1, le=1000),
    current_user: CurrentUser = Depends(get_current_user),
):
    query: dict[str, Any] = {}
    if status:
        query["status"] = status.lower()
    if kind:
        query["kind"] = kind
    jobs = (
        await database.mongodb[os.environ.get("WORKER_DB_NAME", "veriq_worker")]
        .worker_jobs.find(query, {"request.internal_token": 0})
        .sort("updated_at", -1)
        .limit(limit)
        .to_list(limit)
    )
    await record_audit(
        current_user,
        "ADMIN_OPERATIONS_JOBS_VIEWED",
        "platform",
        "operations",
    )
    return APIResponse(data=jobs, message="Tải danh sách tác vụ nền hoàn tất")


@router.post(
    "/quan-tri/van-hanh/tac-vu/{job_id}/thu-lai",
    response_model=APIResponse[Any],
    status_code=202,
)
async def retry_operations_job(
    job_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    worker_url = os.environ.get("WORKER_INTERNAL_URL", "http://worker:8000").rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{worker_url}/xu-ly-nen/noi-bo/tac-vu/{job_id}/thu-lai",
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
            response.raise_for_status()
            result = response.json()
    except httpx.HTTPStatusError as error:
        if error.response.status_code in {404, 409, 422}:
            raise HTTPException(
                status_code=error.response.status_code,
                detail="Tác vụ không tồn tại hoặc không đủ điều kiện chạy lại",
            ) from error
        raise HTTPException(status_code=502, detail="Không thể chạy lại tác vụ nền") from error
    except httpx.HTTPError as error:
        raise HTTPException(status_code=503, detail="Dịch vụ tác vụ nền chưa sẵn sàng") from error
    await record_audit(
        current_user,
        "ADMIN_OPERATIONS_JOB_RETRIED",
        job_id,
        "operations retry",
    )
    return APIResponse(data=result, message="Đưa tác vụ vào hàng đợi chạy lại hoàn tất")


@router.post("/quan-tri/van-hanh/tac-vu/{job_id}/huy", response_model=APIResponse[Any])
async def cancel_operations_job(
    job_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    worker_url = os.environ.get("WORKER_INTERNAL_URL", "http://worker:8000").rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(f"{worker_url}/xu-ly-nen/noi-bo/tac-vu/{job_id}/huy", headers={"X-Internal-Token": settings.SECRET_KEY})
            response.raise_for_status()
            result = response.json()
    except httpx.HTTPStatusError as error:
        if error.response.status_code in {404, 409, 422}:
            raise HTTPException(status_code=error.response.status_code, detail="Tác vụ không tồn tại hoặc không thể hủy") from error
        raise HTTPException(status_code=502, detail="Không thể hủy tác vụ nền") from error
    except httpx.HTTPError as error:
        raise HTTPException(status_code=503, detail="Dịch vụ tác vụ nền chưa sẵn sàng") from error
    await record_audit(current_user, "ADMIN_OPERATIONS_JOB_CANCELED", job_id, "operations cancel")
    return APIResponse(data=result, message="Hủy tác vụ nền hoàn tất")


@router.get("/quan-tri/van-hanh/dlq", response_model=APIResponse[Any])
async def list_dead_letter_jobs(
    limit: int = Query(default=200, ge=1, le=1000),
    current_user: CurrentUser = Depends(get_current_user),
):
    jobs = await database.mongodb[os.environ.get("WORKER_DB_NAME", "veriq_worker")].worker_jobs.find(
        {"status": "failed"}, {"request.internal_token": 0}
    ).sort("updated_at", -1).limit(limit).to_list(limit)
    return APIResponse(data=jobs, message="Tải danh sách tác vụ lỗi hoàn tất")


@router.post("/quan-tri/van-hanh/dlq/{job_id}/loai-bo", response_model=APIResponse[Any])
async def discard_dead_letter_job(
    job_id: str,
    payload: ActionReason,
    current_user: CurrentUser = Depends(get_current_user),
):
    job = await database.mongodb[os.environ.get("WORKER_DB_NAME", "veriq_worker")].worker_jobs.find_one_and_update(
        {"_id": job_id, "status": "failed"},
        {"$set": {"status": "discarded", "discard_reason": payload.reason, "discarded_by": current_user.id, "discarded_at": datetime.now(timezone.utc)}},
        return_document=ReturnDocument.AFTER,
    )
    if not job:
        raise HTTPException(status_code=409, detail="Tác vụ không ở trạng thái lỗi")
    await record_audit(current_user, "ADMIN_DLQ_JOB_DISCARDED", job_id, payload.reason)
    return APIResponse(data=job, message="Loại bỏ tác vụ lỗi hoàn tất")


async def service_health(name: str, url: str):
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(url)
            body = response.json()
            return {
                "service": name,
                "healthy": response.status_code < 400,
                "status_code": response.status_code,
                "details": body,
            }
    except (httpx.HTTPError, ValueError):
        return {
            "service": name,
            "healthy": False,
            "status_code": None,
            "details": {"status": "unavailable"},
        }


@router.get("/quan-tri/suc-khoe", response_model=APIResponse[Any])
async def platform_health(
    current_user: CurrentUser = Depends(get_current_user),
):
    services = {
        "authentication": "http://authentication:8000/san-sang",
        "testing": "http://testing:8000/san-sang",
        "worker": "http://worker:8000/san-sang",
        "ai": "http://ai:8000/san-sang",
        "content": "http://content:8000/san-sang",
    }
    results = await asyncio.gather(
        *(service_health(name, url) for name, url in services.items())
    )
    try:
        await database.mongodb.admin.command("ping")
        mongodb = {"service": "mongodb", "healthy": True, "details": {"status": "ready"}}
    except Exception:
        mongodb = {
            "service": "mongodb",
            "healthy": False,
            "details": {"status": "unavailable"},
        }
    results.append(mongodb)
    await record_audit(
        current_user,
        "ADMIN_PLATFORM_HEALTH_VIEWED",
        "platform",
        "operations",
    )
    return APIResponse(
        data={
            "healthy": all(item["healthy"] for item in results),
            "services": results,
            "checked_at": datetime.now(timezone.utc),
        },
        message="Tải trạng thái vận hành nền tảng hoàn tất",
    )


@router.get("/quan-tri/nhat-ky", response_model=APIResponse[Any])
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


def masked_config(config: dict):
    data = {key: value for key, value in config.items() if key not in {"_id", "type"}}
    for key in list(data):
        if any(marker in key.lower() for marker in ("secret", "token", "password", "credential")):
            data[key] = "Đã cấu hình" if data[key] else None
    return data


async def get_platform_config(config_type: str, current_user: CurrentUser):
    config = await database.mongodb[settings.AUTHENTICATION_DB_NAME].system_configs.find_one(
        {"type": config_type}
    )
    await record_audit(current_user, "ADMIN_CONFIG_VIEWED", config_type, "platform configuration")
    return APIResponse(data=masked_config(config or {"type": config_type}), message="Tải cấu hình nền tảng hoàn tất")


async def update_platform_config(config_type: str, payload: ConfigUpdate, current_user: CurrentUser):
    allowed = {key: value for key, value in payload.values.items() if isinstance(key, str) and len(key) <= 100}
    if not allowed:
        raise HTTPException(status_code=422, detail="Không có cấu hình hợp lệ")
    timestamp = datetime.now(timezone.utc)
    await database.mongodb[settings.AUTHENTICATION_DB_NAME].system_configs.update_one(
        {"type": config_type},
        {"$set": {**allowed, "updated_at": timestamp, "updated_by": current_user.id}, "$setOnInsert": {"type": config_type, "created_at": timestamp}},
        upsert=True,
    )
    await record_audit(current_user, "ADMIN_CONFIG_UPDATED", config_type, payload.reason, {"keys": sorted(allowed)})
    return await get_platform_config(config_type, current_user)


@router.get("/quan-tri/bao-mat/chinh-sach-xac-thuc", response_model=APIResponse[Any])
async def get_auth_policy(current_user: CurrentUser = Depends(get_current_user)):
    return await get_platform_config("security_auth_policy", current_user)


@router.patch("/quan-tri/bao-mat/chinh-sach-xac-thuc", response_model=APIResponse[Any])
async def update_auth_policy(payload: ConfigUpdate, current_user: CurrentUser = Depends(get_current_user)):
    return await update_platform_config("security_auth_policy", payload, current_user)


@router.get("/quan-tri/tich-hop", response_model=APIResponse[Any])
async def get_integrations(current_user: CurrentUser = Depends(get_current_user)):
    return await get_platform_config("integrations", current_user)


@router.patch("/quan-tri/tich-hop", response_model=APIResponse[Any])
async def update_integrations(payload: ConfigUpdate, current_user: CurrentUser = Depends(get_current_user)):
    return await update_platform_config("integrations", payload, current_user)


@router.get("/quan-tri/luu-tru", response_model=APIResponse[Any])
async def get_storage_config(current_user: CurrentUser = Depends(get_current_user)):
    return await get_platform_config("storage", current_user)


@router.patch("/quan-tri/luu-tru", response_model=APIResponse[Any])
async def update_storage_config(payload: ConfigUpdate, current_user: CurrentUser = Depends(get_current_user)):
    return await update_platform_config("storage", payload, current_user)


@router.get("/quan-tri/cau-hinh", response_model=APIResponse[Any])
async def get_system_config(current_user: CurrentUser = Depends(get_current_user)):
    return await get_platform_config("system", current_user)


@router.patch("/quan-tri/cau-hinh", response_model=APIResponse[Any])
async def update_system_config(payload: ConfigUpdate, current_user: CurrentUser = Depends(get_current_user)):
    return await update_platform_config("system", payload, current_user)


@router.get("/quan-tri/ai/mo-hinh", response_model=APIResponse[Any])
async def list_ai_models(current_user: CurrentUser = Depends(get_current_user)):
    models = await database.mongodb[settings.AUTHENTICATION_DB_NAME].ai_models.find({}).sort("model", 1).to_list(500)
    return APIResponse(data=[{**model, "_id": str(model["_id"])} for model in models], message="Tải danh mục mô hình AI hoàn tất")


@router.post("/quan-tri/ai/mo-hinh", response_model=APIResponse[Any], status_code=201)
async def register_ai_model(payload: ModelRegistryEntry, current_user: CurrentUser = Depends(get_current_user)):
    timestamp = datetime.now(timezone.utc)
    model = {
        "provider_id": payload.provider_id,
        "model": payload.model,
        "version": payload.version,
        "enabled": payload.enabled,
        "capabilities": payload.capabilities,
        "created_at": timestamp,
        "updated_at": timestamp,
        "updated_by": current_user.id,
    }
    result = await database.mongodb[settings.AUTHENTICATION_DB_NAME].ai_models.insert_one(model)
    model["_id"] = str(result.inserted_id)
    await record_audit(current_user, "ADMIN_AI_MODEL_REGISTERED", model["_id"], payload.reason)
    return APIResponse(data=model, message="Đăng ký mô hình AI hoàn tất", status=201)


@router.patch("/quan-tri/ai/mo-hinh/{model_id}", response_model=APIResponse[Any])
async def update_ai_model(model_id: str, payload: ConfigUpdate, current_user: CurrentUser = Depends(get_current_user)):
    changes = {key: value for key, value in payload.values.items() if key in {"enabled", "version", "capabilities", "model", "provider_id"}}
    if not changes:
        raise HTTPException(status_code=422, detail="Không có thay đổi mô hình hợp lệ")
    changes["updated_at"] = datetime.now(timezone.utc)
    try:
        from bson import ObjectId
        identifier = ObjectId(model_id)
    except Exception:
        identifier = model_id
    model = await database.mongodb[settings.AUTHENTICATION_DB_NAME].ai_models.find_one_and_update(
        {"_id": identifier}, {"$set": changes}, return_document=ReturnDocument.AFTER
    )
    if not model:
        raise HTTPException(status_code=404, detail="Không tìm thấy mô hình AI")
    model["_id"] = str(model["_id"])
    await record_audit(current_user, "ADMIN_AI_MODEL_UPDATED", model_id, payload.reason, {"keys": sorted(changes)})
    return APIResponse(data=model, message="Cập nhật mô hình AI hoàn tất")


@router.get("/quan-tri/ai/mac-dinh", response_model=APIResponse[Any])
async def get_ai_defaults(current_user: CurrentUser = Depends(get_current_user)):
    return await get_platform_config("ai_defaults", current_user)


@router.patch("/quan-tri/ai/mac-dinh", response_model=APIResponse[Any])
async def update_ai_defaults(payload: ConfigUpdate, current_user: CurrentUser = Depends(get_current_user)):
    allowed_keys = {"chat_model_id", "structured_model_id", "fallback_model_ids", "timeout_seconds", "max_output_tokens", "concurrency"}
    if not set(payload.values) <= allowed_keys:
        raise HTTPException(status_code=422, detail="Cấu hình mặc định AI chứa trường không hợp lệ")
    model_ids = [value for key, value in payload.values.items() if key in {"chat_model_id", "structured_model_id"} and value]
    model_ids.extend(payload.values.get("fallback_model_ids") or [])
    if model_ids:
        identifiers = []
        for model_id in set(model_ids):
            try:
                identifiers.append(ObjectId(model_id))
            except Exception:
                identifiers.append(model_id)
        existing = await database.mongodb[settings.AUTHENTICATION_DB_NAME].ai_models.count_documents({"_id": {"$in": identifiers}, "enabled": True})
        if existing != len(set(model_ids)):
            raise HTTPException(status_code=422, detail="Mô hình mặc định hoặc dự phòng chưa được đăng ký và kích hoạt")
    return await update_platform_config("ai_defaults", payload, current_user)


@router.get("/quan-tri/ai/phien-ban", response_model=APIResponse[Any])
async def get_ai_versions(current_user: CurrentUser = Depends(get_current_user)):
    config = await database.mongodb[settings.AUTHENTICATION_DB_NAME].system_configs.find_one({"type": "ai_defaults"}) or {}
    models = await database.mongodb[settings.AUTHENTICATION_DB_NAME].ai_models.find({"enabled": True}).sort("model", 1).to_list(500)
    return APIResponse(
        data={
            "defaults": masked_config(config),
            "models": [{**item, "_id": str(item["_id"])} for item in models],
            "embedding_model": os.environ.get("EMBEDDING_MODEL"),
            "reranker_model": os.environ.get("RERANKER_MODEL"),
            "service_version": os.environ.get("VERSION"),
        },
        message="Tải phiên bản AI đang hoạt động hoàn tất",
    )


@router.post("/quan-tri/luu-tru/kiem-tra", response_model=APIResponse[Any])
async def test_storage(current_user: CurrentUser = Depends(get_current_user)):
    result = await service_health("cloud", "http://cloud:8000/san-sang")
    await record_audit(current_user, "ADMIN_STORAGE_TESTED", "storage", "connectivity test", {"healthy": result["healthy"]})
    if not result["healthy"]:
        raise HTTPException(status_code=503, detail="Kho lưu trữ chưa sẵn sàng")
    return APIResponse(data=result, message="Kiểm tra kho lưu trữ hoàn tất")


@router.get("/quan-tri/tich-hop/suc-khoe", response_model=APIResponse[Any])
async def integration_health(current_user: CurrentUser = Depends(get_current_user)):
    targets = {
        "worker": "http://worker:8000/san-sang",
        "ai": "http://ai:8000/san-sang",
        "cloud": "http://cloud:8000/san-sang",
        "testing": "http://testing:8000/san-sang",
    }
    services = await asyncio.gather(*(service_health(name, url) for name, url in targets.items()))
    try:
        await database.mongodb.admin.command("ping")
        services.append({"service": "mongodb", "healthy": True, "status_code": 200, "details": {"status": "ready"}})
    except Exception:
        services.append({"service": "mongodb", "healthy": False, "status_code": None, "details": {"status": "unavailable"}})
    return APIResponse(data={"healthy": all(item["healthy"] for item in services), "services": services}, message="Tải trạng thái tích hợp hoàn tất")


@router.get("/quan-tri/van-hanh/so-lieu", response_model=APIResponse[Any])
async def operations_metrics(current_user: CurrentUser = Depends(get_current_user)):
    worker_db = database.mongodb[os.environ.get("WORKER_DB_NAME", "veriq_worker")]
    testing_db = database.mongodb[os.environ.get("TESTING_DB_NAME", "veriq_testing")]
    status_rows = await worker_db.worker_jobs.aggregate([{"$group": {"_id": "$status", "count": {"$sum": 1}}}]).to_list(100)
    return APIResponse(
        data={
            "jobs_by_status": {item["_id"]: item["count"] for item in status_rows},
            "impact_analyses": await testing_db.impact_analyses.count_documents({}),
            "degraded_impact_analyses": await testing_db.impact_analyses.count_documents({"mode": "DEGRADED_AI"}),
            "pending_proposals": await testing_db.maintenance_proposals.count_documents({"status": "PENDING"}),
            "generated_at": datetime.now(timezone.utc),
        },
        message="Tải số liệu vận hành hoàn tất",
    )


@router.get("/quan-tri/nhat-ky/xuat")
async def export_global_audit(current_user: CurrentUser = Depends(get_current_user)):
    events = await database.mongodb[settings.AUTHENTICATION_DB_NAME].audit_logs.find({}).sort("timestamp", -1).limit(100000).to_list(100000)
    stream = io.StringIO()
    fields = ["timestamp", "action", "actor_email", "target_user_id", "reason"]
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for event in events:
        writer.writerow({field: event.get(field) for field in fields})
    await record_audit(current_user, "ADMIN_GLOBAL_AUDIT_EXPORTED", "platform", "audit export")
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=veriq-global-audit.csv"})
