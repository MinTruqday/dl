import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from loguru import logger

from src.repositories.storage import file_request_repository
from src.schemas.storage import FileRequestCreate, FileRequestResponse


class FileRequestService:
    @staticmethod
    async def create_request(
        req: FileRequestCreate, owner_id: str
    ) -> Optional[FileRequestResponse]:
        try:
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=req.expires_in_hours)

            doc = {
                "token": token,
                "target_folder_id": req.target_folder_id,
                "owner_id": owner_id,
                "password": req.password,
                "expires_at": expires_at,
                "description": req.description,
                "created_at": datetime.now(timezone.utc),
            }

            await file_request_repository.insert(doc)

            return FileRequestResponse(
                token=token,
                target_folder_id=req.target_folder_id,
                owner_id=owner_id,
                description=req.description,
                expires_at=expires_at,
                is_protected=bool(req.password),
            )
        except Exception as e:
            logger.error(f"Failed to create file request: {e}")
            return None

    @staticmethod
    async def validate_request(token: str, password: Optional[str] = None) -> Optional[dict]:
        try:
            doc = await file_request_repository.find(token)
            if not doc:
                return None

            if doc["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                return None

            if doc.get("password") and doc["password"] != password:
                return {"error": "Mật khẩu không chính xác"}

            return {
                "target_folder_id": doc["target_folder_id"],
                "owner_id": doc["owner_id"],
                "description": doc.get("description"),
            }
        except Exception as e:
            logger.error(f"Failed to validate file request: {e}")
            return None
