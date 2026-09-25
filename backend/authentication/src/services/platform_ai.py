from datetime import datetime, timezone

import httpx
from fastapi import HTTPException

from src.clients.service_gateway import health_request
from src.core.dependency import CurrentUser
from src.core.infrastructure.configuration import settings
from src.core.policies import platform_policy
from src.repositories.identity import IdentityRepository
from src.repositories.platform import PlatformRepository
from src.schemas.platform import ConfigUpdate, ModelRegistryEntry, ProviderUpdate
from src.services.platform import (
    get_platform_config,
    masked_config,
    record_audit,
    update_platform_config,
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


class PlatformAiService:
    @staticmethod
    async def providers():
        providers = await PlatformRepository.list_ai_providers()
        if not providers:
            providers = [
                {
                    "_id": settings.AI_PROVIDER,
                    "enabled": True,
                    "model": settings.LLM_MODEL,
                    "timeout_seconds": settings.MODEL_TIMEOUT_SECONDS,
                    "max_output_tokens": settings.AGENT_DEFAULT_MAX_OUTPUT_TOKENS,
                    "secret_reference": settings.AI_PROVIDER_CONFIGURED,
                    "requires_restart": False,
                }
            ]
        return [provider_view(provider) for provider in providers]

    @staticmethod
    async def update_provider(
        provider_id: str, payload: ProviderUpdate, current_user: CurrentUser
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
        provider = await PlatformRepository.upsert_ai_provider(
            provider_id, changes, timestamp
        )
        await record_audit(
            current_user, "ADMIN_AI_PROVIDER_UPDATED", provider_id, payload.reason
        )
        return provider_view(provider)

    @staticmethod
    async def test_provider(provider_id: str, current_user: CurrentUser):
        try:
            response = await health_request("ai")
            response.raise_for_status()
            health = response.json()
        except httpx.HTTPError as error:
            await record_audit(
                current_user, "ADMIN_AI_PROVIDER_TEST_FAILED", provider_id, "health test"
            )
            raise HTTPException(status_code=503, detail="Nhà cung cấp AI chưa sẵn sàng") from error
        await record_audit(
            current_user, "ADMIN_AI_PROVIDER_TESTED", provider_id, "health test"
        )
        return {"provider_id": provider_id, "healthy": True, "service": health}

    @staticmethod
    async def models():
        models = await PlatformRepository.list_ai_models()
        return [{**model, "_id": str(model["_id"])} for model in models]

    @staticmethod
    async def register_model(payload: ModelRegistryEntry, current_user: CurrentUser):
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
        result = await PlatformRepository.insert_ai_model(model)
        model["_id"] = str(result.inserted_id)
        await record_audit(
            current_user, "ADMIN_AI_MODEL_REGISTERED", model["_id"], payload.reason
        )
        return model

    @staticmethod
    async def update_model(model_id: str, payload: ConfigUpdate, current_user: CurrentUser):
        allowed_keys = set(platform_policy()["ai"]["model_update_allowed_keys"])
        changes = {
            key: value
            for key, value in payload.values.items()
            if key in allowed_keys
        }
        if not changes:
            raise HTTPException(status_code=422, detail="Không có thay đổi mô hình hợp lệ")
        changes["updated_at"] = datetime.now(timezone.utc)
        model = await PlatformRepository.update_ai_model(model_id, changes)
        if not model:
            raise HTTPException(status_code=404, detail="Không tìm thấy mô hình AI")
        model["_id"] = str(model["_id"])
        await record_audit(
            current_user,
            "ADMIN_AI_MODEL_UPDATED",
            model_id,
            payload.reason,
            {"keys": sorted(changes)},
        )
        return model

    @staticmethod
    async def defaults(current_user: CurrentUser):
        return await get_platform_config("ai_defaults", current_user)

    @staticmethod
    async def update_defaults(payload: ConfigUpdate, current_user: CurrentUser):
        policy = platform_policy()["ai"]
        allowed_keys = set(policy["default_allowed_keys"])
        if not set(payload.values) <= allowed_keys:
            raise HTTPException(
                status_code=422, detail="Cấu hình mặc định AI chứa trường không hợp lệ"
            )
        model_ids = [
            value
            for key, value in payload.values.items()
            if key in policy["primary_model_reference_keys"] and value
        ]
        model_ids.extend(payload.values.get("fallback_model_ids") or [])
        if model_ids:
            unique_model_ids = list(set(model_ids))
            existing = await PlatformRepository.count_ai_models(unique_model_ids)
            if existing != len(set(model_ids)):
                raise HTTPException(
                    status_code=422,
                    detail="Mô hình mặc định hoặc dự phòng chưa được đăng ký và kích hoạt",
                )
        return await update_platform_config("ai_defaults", payload, current_user)

    @staticmethod
    async def versions():
        config = await IdentityRepository.get_system_config_by_type("ai_defaults") or {}
        models = await PlatformRepository.list_ai_models({"enabled": True})
        return {
            "defaults": masked_config(config),
            "models": [{**item, "_id": str(item["_id"])} for item in models],
            "embedding_model": settings.EMBEDDING_MODEL,
            "reranker_model": settings.RERANKER_MODEL,
            "service_version": settings.VERSION,
        }
