from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import HTTPException

from src.core.dependency import CurrentUser
from src.core.policies import platform_policy
from src.repositories.identity import IdentityRepository
from src.repositories.platform import PlatformRepository
from src.schemas.platform import (
    ActionReason,
    EmergencyRevokeRequest,
    SecretReferenceRequest,
    SecretReferenceRotateRequest,
    ServiceIdentityRequest,
    ServiceIdentityRotateRequest,
)
from src.services.platform import account_or_404, record_audit


SECURITY_POLICY = platform_policy()["platform_security"]


def masked_reference(value: dict):
    return {
        **{
            key: item for key, item in value.items() if key not in {"reference", "secret_reference"}
        },
        **({"reference": "Đã cấu hình"} if value.get("reference") else {}),
        **({"secret_reference": "Đã cấu hình"} if value.get("secret_reference") else {}),
    }


class PlatformSecurityService:
    @staticmethod
    async def service_identities():
        values = await PlatformRepository.list_service_identities()
        return [masked_reference(value) for value in values]

    @staticmethod
    async def create_service_identity(payload: ServiceIdentityRequest, current_user: CurrentUser):
        timestamp = datetime.now(timezone.utc)
        value = {
            "_id": f"service-{uuid4().hex}",
            "name": payload.name,
            "secret_reference": payload.secret_reference,
            "scopes": sorted(set(payload.scopes)),
            "status": SECURITY_POLICY["active_status"],
            "revision": 1,
            "created_by": current_user.id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        await PlatformRepository.insert_service_identity(value)
        await record_audit(
            current_user,
            "ADMIN_SERVICE_IDENTITY_CREATED",
            value["_id"],
            payload.reason,
            {"scopes": value["scopes"]},
        )
        return masked_reference(value)

    @staticmethod
    async def rotate_service_identity(
        identity_id: str, payload: ServiceIdentityRotateRequest, current_user: CurrentUser
    ):
        value = await PlatformRepository.rotate_service_identity(
            identity_id,
            {
                "secret_reference": payload.secret_reference,
                "rotated_at": datetime.now(timezone.utc),
                "updated_by": current_user.id,
            },
            SECURITY_POLICY["revoked_status"],
        )
        if not value:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh tính dịch vụ")
        await record_audit(
            current_user, "ADMIN_SERVICE_IDENTITY_ROTATED", identity_id, payload.reason
        )
        return masked_reference(value)

    @staticmethod
    async def emergency_revoke(payload: EmergencyRevokeRequest, current_user: CurrentUser):
        affected = 0
        timestamp = datetime.now(timezone.utc)
        if payload.scope == "USER":
            await account_or_404(payload.target_id or "")
            await IdentityRepository.revoke_all_sessions(payload.target_id or "")
            affected = 1
        elif payload.scope == "ALL_USERS":
            result = await IdentityRepository.revoke_every_session(timestamp)
            affected = result.modified_count
            await IdentityRepository.clear_every_session_cache()
        elif payload.scope == "SERVICE_IDENTITY":
            result = await PlatformRepository.update_service_identities(
                {"_id": payload.target_id},
                {
                    "status": SECURITY_POLICY["revoked_status"],
                    "revoked_at": timestamp,
                    "revoked_by": current_user.id,
                },
            )
            affected = result.modified_count
        else:
            result = await PlatformRepository.update_service_identities(
                {"status": {"$ne": SECURITY_POLICY["revoked_status"]}},
                {
                    "status": SECURITY_POLICY["revoked_status"],
                    "revoked_at": timestamp,
                    "revoked_by": current_user.id,
                },
                many=True,
            )
            affected = result.modified_count
        await record_audit(
            current_user,
            "ADMIN_EMERGENCY_REVOKE",
            payload.target_id or "platform",
            payload.reason,
            {"scope": payload.scope, "affected": affected},
        )
        return {"scope": payload.scope, "affected": affected}

    @staticmethod
    async def audit(action: str, actor: str, limit: int):
        query: dict[str, Any] = {}
        if action:
            query["action"] = {"$regex": action, "$options": "i"}
        if actor:
            query["actor_email"] = {"$regex": actor, "$options": "i"}
        values = await PlatformRepository.list_audit_logs(query, limit)
        return [{**value, "_id": str(value["_id"])} for value in values]

    @staticmethod
    async def secret_references():
        values = await PlatformRepository.list_secret_references()
        return [masked_reference(value) for value in values]

    @staticmethod
    async def create_secret_reference(payload: SecretReferenceRequest, current_user: CurrentUser):
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
        await PlatformRepository.insert_secret_reference(value)
        await record_audit(
            current_user,
            "ADMIN_SECRET_REFERENCE_CREATED",
            value["_id"],
            payload.reason,
            {"provider": payload.provider},
        )
        return masked_reference(value)

    @staticmethod
    async def rotate_secret_reference(
        reference_id: str, payload: SecretReferenceRotateRequest, current_user: CurrentUser
    ):
        value = await PlatformRepository.rotate_secret_reference(
            reference_id,
            {
                "reference": payload.reference,
                "rotated_at": datetime.now(timezone.utc),
                "updated_by": current_user.id,
            },
        )
        if not value:
            raise HTTPException(status_code=404, detail="Không tìm thấy tham chiếu bí mật")
        await record_audit(
            current_user, "ADMIN_SECRET_REFERENCE_ROTATED", reference_id, payload.reason
        )
        return masked_reference(value)

    @staticmethod
    async def delete_secret_reference(
        reference_id: str, payload: ActionReason, current_user: CurrentUser
    ):
        if await PlatformRepository.count_service_identities(
            {"secret_reference": reference_id, "status": SECURITY_POLICY["active_status"]}
        ):
            raise HTTPException(status_code=409, detail="Tham chiếu bí mật đang được sử dụng")
        result = await PlatformRepository.delete_secret_reference(reference_id)
        if not result.deleted_count:
            raise HTTPException(status_code=404, detail="Không tìm thấy tham chiếu bí mật")
        await record_audit(
            current_user, "ADMIN_SECRET_REFERENCE_DELETED", reference_id, payload.reason
        )
        return {"reference_id": reference_id, "deleted": True}
