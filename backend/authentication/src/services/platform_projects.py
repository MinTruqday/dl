from datetime import datetime, timezone

import httpx
from fastapi import HTTPException

from src.clients.service_gateway import internal_request
from src.core.dependency import CurrentUser
from src.core.policies import platform_policy
from src.repositories.identity import IdentityRepository
from src.schemas.platform import (
    ActionReason,
    BreakGlassCreateRequest,
    ProjectDeleteRequest,
    ProjectPolicyUpdate,
    ProjectQuotaUpdate,
    ProjectStatusUpdate,
)
from src.services.platform import account_or_404, record_audit

PROJECT_POLICY = platform_policy()["projects"]


class PlatformProjectService:
    @staticmethod
    async def list(search: str, status: str, limit: int, current_user: CurrentUser):
        response = await internal_request(
            "GET",
            "testing",
            "/kiem-thu/noi-bo/quan-tri/du-an",
            params={"search": search, "status": status, "limit": limit},
        )
        response.raise_for_status()
        await record_audit(
            current_user, PROJECT_POLICY["audit_actions"]["metadata_viewed"], "platform", "operations"
        )
        return response.json()

    @staticmethod
    async def detail(project_id: str, current_user: CurrentUser):
        response = await internal_request(
            "GET", "testing", f"/kiem-thu/noi-bo/quan-tri/du-an/{project_id}"
        )
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
        response.raise_for_status()
        project = response.json()
        try:
            response = await internal_request(
                "GET",
                "worker",
                "/xu-ly-nen/noi-bo/tong-quan",
                params={"project_id": project_id},
            )
            response.raise_for_status()
            project["job_count"] = response.json()["total"]
        except (httpx.HTTPError, KeyError, ValueError):
            project["job_count"] = None
        await record_audit(
            current_user,
            PROJECT_POLICY["audit_actions"]["metadata_viewed"],
            project_id,
            "support metadata",
        )
        return project

    @staticmethod
    async def update_status(
        project_id: str, payload: ProjectStatusUpdate, current_user: CurrentUser
    ):
        response = await internal_request(
            "PATCH",
            "testing",
            f"/kiem-thu/noi-bo/quan-tri/du-an/{project_id}/trang-thai",
            payload={
                "status": payload.status,
                "reason": payload.reason,
                "actor_id": current_user.id,
            },
        )
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
        response.raise_for_status()
        await record_audit(
            current_user,
            PROJECT_POLICY["audit_actions"]["status_updated"],
            project_id,
            payload.reason,
            {"status": payload.status},
        )
        return response.json()

    @staticmethod
    async def update_quota(
        project_id: str, payload: ProjectQuotaUpdate, current_user: CurrentUser
    ):
        quota = payload.model_dump(exclude={"reason"}, exclude_none=True)
        if not quota:
            raise HTTPException(status_code=422, detail="Không có hạn mức cần cập nhật")
        response = await internal_request(
            "PATCH",
            "testing",
            f"/kiem-thu/noi-bo/quan-tri/du-an/{project_id}/han-muc",
            payload={"quota": quota, "actor_id": current_user.id},
        )
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
        response.raise_for_status()
        await record_audit(
            current_user,
            PROJECT_POLICY["audit_actions"]["quota_updated"],
            project_id,
            payload.reason,
            quota,
        )
        return {"project_id": project_id, "quota": quota}

    @staticmethod
    async def policy():
        config = await IdentityRepository.get_system_config_by_type(
            PROJECT_POLICY["creation_config_type"]
        )
        return {
            "project_creation_policy": (config or {}).get(
                "project_creation_policy", PROJECT_POLICY["default_creation_policy"]
            ),
            "updated_at": (config or {}).get("updated_at"),
        }

    @staticmethod
    async def update_policy(payload: ProjectPolicyUpdate, current_user: CurrentUser):
        timestamp = datetime.now(timezone.utc)
        await IdentityRepository.update_system_config(
            PROJECT_POLICY["creation_config_type"],
            {
                "$set": {
                    "project_creation_policy": payload.project_creation_policy,
                    "updated_at": timestamp,
                    "updated_by": current_user.id,
                },
                "$setOnInsert": {
                    "type": PROJECT_POLICY["creation_config_type"],
                    "created_at": timestamp,
                },
            },
            upsert=True,
        )
        await record_audit(
            current_user,
            PROJECT_POLICY["audit_actions"]["policy_updated"],
            "platform",
            payload.reason,
            {"project_creation_policy": payload.project_creation_policy},
        )
        return {"project_creation_policy": payload.project_creation_policy}

    @staticmethod
    async def membership_diagnostics(project_id: str, current_user: CurrentUser):
        response = await internal_request(
            "GET", "testing", f"/kiem-thu/noi-bo/quan-tri/du-an/{project_id}/thanh-vien"
        )
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
        response.raise_for_status()
        await record_audit(
            current_user,
            PROJECT_POLICY["audit_actions"]["memberships_viewed"],
            project_id,
            "support metadata",
        )
        return response.json()

    @staticmethod
    async def hard_delete(
        project_id: str, payload: ProjectDeleteRequest, current_user: CurrentUser
    ):
        response = await internal_request(
            "DELETE",
            "testing",
            f"/kiem-thu/noi-bo/quan-tri/du-an/{project_id}",
            payload={"confirmation": payload.confirmation},
            timeout=60,
        )
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
        if response.status_code == 422:
            raise HTTPException(status_code=422, detail="Xác nhận phải khớp mã dự án")
        response.raise_for_status()
        result = response.json()
        await record_audit(
            current_user,
            PROJECT_POLICY["audit_actions"]["hard_deleted"],
            project_id,
            payload.reason,
            {"project_key": result.get("project_key"), "deleted": result["deleted"]},
        )
        return {"project_id": project_id, "deleted": result["deleted"]}

    @staticmethod
    async def break_glass_grants(active_only: bool):
        response = await internal_request(
            "GET",
            "testing",
            "/kiem-thu/noi-bo/quan-tri/truy-cap-khan-cap",
            params={"active_only": active_only},
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    async def create_break_glass(
        payload: BreakGlassCreateRequest, current_user: CurrentUser
    ):
        await account_or_404(payload.user_id)
        response = await internal_request(
            "POST",
            "testing",
            "/kiem-thu/noi-bo/quan-tri/truy-cap-khan-cap",
            payload={**payload.model_dump(), "actor_id": current_user.id},
        )
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
        response.raise_for_status()
        grant = response.json()
        await record_audit(
            current_user,
            PROJECT_POLICY["audit_actions"]["break_glass_granted"],
            grant["_id"],
            payload.reason,
            {
                "project_id": payload.project_id,
                "user_id": payload.user_id,
                "permissions": grant["permissions"],
            },
        )
        return grant

    @staticmethod
    async def revoke_break_glass(
        grant_id: str, payload: ActionReason, current_user: CurrentUser
    ):
        response = await internal_request(
            "POST",
            "testing",
            f"/kiem-thu/noi-bo/quan-tri/truy-cap-khan-cap/{grant_id}/thu-hoi",
            payload={"reason": payload.reason, "actor_id": current_user.id},
        )
        if response.status_code == 409:
            raise HTTPException(status_code=409, detail="Quyền truy cập khẩn cấp không còn hoạt động")
        response.raise_for_status()
        grant = response.json()
        await record_audit(
            current_user, PROJECT_POLICY["audit_actions"]["break_glass_revoked"], grant_id, payload.reason
        )
        return grant
