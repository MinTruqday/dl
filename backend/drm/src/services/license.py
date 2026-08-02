import base64
import datetime
import os
import uuid
from datetime import timedelta

from src.core.logic_logger import log_logic_execution
from src.repositories.license import LicenseRepository

class LicenseService:
    @staticmethod
    @log_logic_execution
    async def create_license(document_id: str, user_id: str) -> tuple[str, bytes]:
        file_id = str(uuid.uuid4())
        raw_key = os.urandom(32)
        encoded_key = base64.b64encode(raw_key).decode("utf-8")
        
        now = datetime.datetime.now(datetime.timezone.utc)
        settings_doc = await LicenseRepository.get_drm_settings(document_id) or {}
        valid_days = max(1, min(int(settings_doc.get("license_valid_days", 30)), 365))
        max_open_count = max(1, min(int(settings_doc.get("max_open_count", 100)), 10000))
        await LicenseRepository.create_license(
            {
                "file_id": file_id,
                "aes_key": encoded_key,
                "document_id": document_id,
                "user_id": user_id,
                "created_at": now,
                "expires_at": now + timedelta(days=valid_days),
                "status": "ACTIVE",
                "open_count": 0,
                "max_open_count": max_open_count,
                "payload_format": "pdf",
                "profile": "doclib-drm-2026",
                "content_encryption": "AES-256-GCM",
                "rights": {
                    "copy": not settings_doc.get("disable_copy", True),
                    "print": not settings_doc.get("disable_print", True),
                    "internal_ai": settings_doc.get("allow_internal_ai", True),
                },
            }
        )
        return file_id, raw_key
