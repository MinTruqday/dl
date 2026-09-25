import hashlib
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException

from src.core.dependency import CurrentUser
from src.core.infrastructure.configuration import settings
from src.core.policies import platform_policy
from src.repositories.identity import IdentityRepository
from src.repositories.platform import PlatformRepository
from src.schemas.platform import (
    ActionReason,
    BulkUserPreviewRequest,
    UserDeleteRequest,
)
from src.services.platform import account_or_404, protect_last_admin, record_audit
from src.services.session import SessionService

ACCOUNT_CONTROL_POLICY = platform_policy()["account_controls"]


class PlatformAccountControlService:
    @staticmethod
    async def resend_activation(
        user_id: str, payload: ActionReason, client_ip: str, current_user: CurrentUser
    ):
        account = await account_or_404(user_id)
        await SessionService.forgot_password(account["email"], client_ip)
        await record_audit(
            current_user, ACCOUNT_CONTROL_POLICY["activation_resent_audit_action"], user_id, payload.reason
        )
        return {"user_id": user_id, "delivery_status": ACCOUNT_CONTROL_POLICY["activation_delivery_status"]}

    @staticmethod
    async def anonymize(
        user_id: str, payload: UserDeleteRequest, current_user: CurrentUser
    ):
        account = await account_or_404(user_id)
        if payload.confirmation != account.get("email"):
            raise HTTPException(status_code=422, detail="Xác nhận phải khớp email tài khoản")
        if user_id == current_user.id:
            raise HTTPException(
                status_code=422, detail="Không thể tự xóa tài khoản quản trị hiện tại"
            )
        await protect_last_admin(account, desired_active=False)
        timestamp = datetime.now(timezone.utc)
        digest = hashlib.sha256(f"{user_id}:{timestamp.isoformat()}".encode()).hexdigest()[:24]
        await IdentityRepository.update_auth_credential(
            {"_id": user_id},
            {
                "$set": {
                    "email": f"{ACCOUNT_CONTROL_POLICY['deleted_email_prefix']}{digest}{ACCOUNT_CONTROL_POLICY['deleted_email_suffix']}",
                    "slug": f"{ACCOUNT_CONTROL_POLICY['deleted_email_prefix']}{digest}",
                    "full_name": ACCOUNT_CONTROL_POLICY["deleted_full_name"],
                    "is_active": False,
                    "account_status": ACCOUNT_CONTROL_POLICY["deleted_status"],
                    "system_role": ACCOUNT_CONTROL_POLICY["default_system_role"],
                    "permissions": [],
                    "passkeys": [],
                    "deleted_at": timestamp,
                    "deleted_by": current_user.id,
                    "updated_at": timestamp,
                },
                "$unset": {field: "" for field in ACCOUNT_CONTROL_POLICY["sensitive_account_fields"]},
            },
        )
        await IdentityRepository.revoke_all_sessions(user_id)
        await record_audit(
            current_user, ACCOUNT_CONTROL_POLICY["anonymized_audit_action"], user_id, payload.reason
        )
        return {"user_id": user_id, "status": ACCOUNT_CONTROL_POLICY["deleted_status"], "anonymized": True}

    @staticmethod
    async def preview_bulk(payload: BulkUserPreviewRequest, current_user: CurrentUser):
        user_ids = list(dict.fromkeys(payload.user_ids))
        accounts = await IdentityRepository.find_auth_credentials(
            {"_id": {"$in": user_ids}},
            {"email": 1, "is_active": 1, "account_status": 1},
            len(user_ids),
        )
        now = datetime.now(timezone.utc)
        operation = {
            "_id": f"{ACCOUNT_CONTROL_POLICY['bulk_operation_identifier_prefix']}{uuid4().hex}",
            "kind": ACCOUNT_CONTROL_POLICY["bulk_operation_kind"],
            "action": payload.action,
            "user_ids": [item["_id"] for item in accounts],
            "requested_user_ids": user_ids,
            "missing_user_ids": sorted(set(user_ids) - {item["_id"] for item in accounts}),
            "reason": payload.reason,
            "status": ACCOUNT_CONTROL_POLICY["bulk_preview_status"],
            "created_by": current_user.id,
            "created_at": now,
            "expires_at": now + timedelta(minutes=settings.ADMIN_OPERATION_EXPIRE_MINUTES),
        }
        await PlatformRepository.insert_admin_operation(operation)
        return {**operation, "accounts": accounts}

    @staticmethod
    async def confirm_bulk(operation_id: str, current_user: CurrentUser):
        now = datetime.now(timezone.utc)
        operation = await PlatformRepository.claim_admin_operation(
            {
                "_id": operation_id,
                "kind": ACCOUNT_CONTROL_POLICY["bulk_operation_kind"],
                "status": ACCOUNT_CONTROL_POLICY["bulk_preview_status"],
                "created_by": current_user.id,
                "expires_at": {"$gt": now},
            },
            now,
        )
        if not operation:
            raise HTTPException(
                status_code=409, detail="Bản xem trước không tồn tại đã hết hạn hoặc đã dùng"
            )
        user_ids = [item for item in operation["user_ids"] if item != current_user.id]
        affected = 0
        if operation["action"] == ACCOUNT_CONTROL_POLICY["disable_action"]:
            accounts = await IdentityRepository.find_auth_credentials(
                {"_id": {"$in": user_ids}}, limit=len(user_ids)
            )
            for account in accounts:
                await protect_last_admin(account, desired_active=False)
            result = await IdentityRepository.update_auth_credentials(
                {"_id": {"$in": user_ids}},
                {
                    "$set": {
                        "is_active": False,
                        "account_status": ACCOUNT_CONTROL_POLICY["disabled_status"],
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
            affected = result.modified_count
            for user_id in user_ids:
                await IdentityRepository.revoke_all_sessions(user_id)
        elif operation["action"] == ACCOUNT_CONTROL_POLICY["revoke_sessions_action"]:
            for user_id in user_ids:
                await IdentityRepository.revoke_all_sessions(user_id)
                affected += 1
        else:
            accounts = await IdentityRepository.find_auth_credentials(
                {"_id": {"$in": user_ids}}, {"email": 1}, len(user_ids)
            )
            for account in accounts:
                await SessionService.forgot_password(
                    account["email"], ACCOUNT_CONTROL_POLICY["bulk_password_reset_client_ip"]
                )
                affected += 1
        await PlatformRepository.complete_admin_operation(
            operation_id, affected, datetime.now(timezone.utc)
        )
        await record_audit(
            current_user,
            ACCOUNT_CONTROL_POLICY["bulk_completed_audit_action"],
            operation_id,
            operation["reason"],
            {"action": operation["action"], "affected": affected},
        )
        return {
            "operation_id": operation_id,
            "status": ACCOUNT_CONTROL_POLICY["completed_status"],
            "affected": affected,
        }
