import httpx
from fastapi import HTTPException

from src.clients.service_gateway import health_request, internal_request
from src.core.dependency import CurrentUser
from src.core.infrastructure.configuration import settings
from src.core.policies import platform_policy
from src.repositories.cache import CacheRepository
from src.schemas.platform import CacheClearRequest, RagReindexRequest
from src.services.platform import record_audit


class PlatformControlOperationsService:
    @staticmethod
    async def request_rag_reindex(payload: RagReindexRequest, current_user: CurrentUser):
        policy = platform_policy()["control_operations"]
        candidates_response = await internal_request(
            "POST",
            "testing",
            "/kiem-thu/noi-bo/quan-tri/rag/ung-vien",
            payload={
                "project_id": payload.project_id,
                "artifact_version_ids": payload.artifact_version_ids,
            },
        )
        if candidates_response.status_code == 404:
            raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
        candidates_response.raise_for_status()
        artifact_ids = candidates_response.json()["artifact_version_ids"]
        accepted = []
        for artifact_id in artifact_ids:
            request_body = {
                "event": "knowledge.index.requested",
                "project_id": payload.project_id,
                "artifact_version_id": artifact_id,
                "model_version": policy["rag_reindex_model_version"],
                "requester_id": current_user.id,
                "requester_email": current_user.email,
                "payload": {},
            }
            try:
                response = await internal_request(
                    "POST",
                    "worker",
                    "/xu-ly-nen/noi-bo/kiem-thu/tac-vu",
                    payload=request_body,
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
        return {"project_id": payload.project_id, "jobs": accepted}

    @staticmethod
    async def inspect_caches():
        policy = platform_policy()["control_operations"]
        counts = {}
        for name in policy["inspect_cache_scopes"]:
            counts[name] = await CacheRepository.count_patterns(
                policy["cache_patterns"][name]
            )
        return counts

    @staticmethod
    async def clear_caches(payload: CacheClearRequest, current_user: CurrentUser):
        patterns = platform_policy()["control_operations"]["cache_patterns"][payload.scope]
        deleted = await CacheRepository.delete_patterns(patterns)
        await record_audit(
            current_user,
            "ADMIN_SAFE_CACHE_CLEARED",
            payload.scope,
            payload.reason,
            {"deleted": deleted},
        )
        return {"scope": payload.scope, "deleted": deleted}

    @staticmethod
    async def runtime_versions():
        policy = platform_policy()["control_operations"]
        results = []
        for name in policy["runtime_services"]:
            try:
                response = await health_request(name)
                results.append(
                    {
                        "service": name,
                        "healthy": response.status_code < 400,
                        "runtime_version": settings.VERSION,
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
        return {
            "services": results,
            "schema_version": settings.VERSION,
            "platform_version": settings.VERSION,
        }
