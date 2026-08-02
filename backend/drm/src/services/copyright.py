from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
from datetime import datetime, timezone
from src.services.content_client import ContentClient
from src.repositories.copyright import CopyrightRepository
from loguru import logger
from fastapi import HTTPException
import hashlib
import secrets


class CopyrightService:
    @staticmethod
    @log_logic_execution
    async def resolve_copyright_dispute(dispute_id: str, resolution: str, current_user) -> dict:
        result = await CopyrightRepository.update_dispute(
            {"_id": dispute_id},
            {
                "$set": {
                    "status": "resolved",
                    "resolution": resolution,
                    "resolved_by": str(current_user.id),
                    "resolved_at": datetime.now(timezone.utc),
                }
            },
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy tranh chấp bản quyền")
        logger.info("Copyright dispute resolved")
        return {"message": "Đã giải quyết tranh chấp bản quyền"}

    @staticmethod
    @log_logic_execution
    async def update_drm_settings(document_id: str, values: dict, current_user) -> dict:
        user_id = str(current_user.id)
        from src.core.dependency import Role

        is_admin = getattr(current_user.role, "value", current_user.role) == Role.ADMIN.value
        document = await ContentClient.get_accessible(document_id, user_id, is_admin, edit=True)
        if not document:
            raise HTTPException(
                status_code=403, detail="Bạn không có quyền cấu hình DRM cho tài liệu này"
            )
        tier = str(getattr(current_user, "tier", "BASIC")).upper()
        if tier == "PRO":
            values = {
                "disable_copy": False,
                "disable_print": False,
                "hide_from_search": False,
                "watermark_enabled": bool(values.get("watermark_enabled", True)),
                "allow_internal_ai": True,
                "license_valid_days": 30,
                "max_open_count": 100,
                "ghost_font_enabled": False,
                "ghost_font_exemption_scope": "everyone",
                "ghost_font_exempt_user_ids": [],
            }
        elif tier == "PREMIUM":
            values["ghost_font_enabled"] = bool(values.get("ghost_font_enabled", True))
            values["ghost_font_exempt_user_ids"] = list(
                dict.fromkeys(
                    str(user_id).strip()
                    for user_id in values.get("ghost_font_exempt_user_ids", [])
                    if str(user_id).strip()
                )
            )[:100]
        else:
            values = {
                "disable_copy": False,
                "disable_print": False,
                "hide_from_search": False,
                "watermark_enabled": False,
                "allow_internal_ai": True,
                "license_valid_days": 30,
                "max_open_count": 100,
                "ghost_font_enabled": False,
                "ghost_font_exemption_scope": "everyone",
                "ghost_font_exempt_user_ids": [],
            }
        values["protection_tier"] = tier
        private_link_token = None
        if tier == "PREMIUM" and values.get("ghost_font_exemption_scope") == "private_link":
            private_link_token = secrets.token_urlsafe(32)
            values["ghost_font_private_link_hash"] = hashlib.sha256(
                private_link_token.encode("utf-8")
            ).hexdigest()
        profile = (
            "doclib-drm-2026"
            if tier == "PREMIUM"
            else "doclib-watermark"
            if tier == "PRO"
            else "doclib-standard"
        )
        await mongo.update_one(
            "document_drm_settings",
            {"document_id": document_id},
            {
                "$set": {
                    **values,
                    "profile": profile,
                    "content_encryption": "AES-256-GCM",
                    "text_delivery": "encrypted_or_rendered",
                    "updated_by": str(current_user.id),
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )
        await ContentClient.update_drm_policy(document_id, values)
        response = {
            "document_id": document_id,
            **values,
            "profile": profile,
            "content_encryption": "AES-256-GCM",
            "text_delivery": "encrypted_or_rendered",
        }
        if private_link_token:
            response["ghost_font_private_link_token"] = private_link_token
        return response
