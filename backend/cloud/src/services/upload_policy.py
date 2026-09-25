import json
import re
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from src.core.infrastructure.configuration import settings
from src.core.storage import get_bucket, get_storage_client
from src.repositories.storage import storage_repository
from src.repositories.storage import temporary_file_repository
from src.repositories.storage import upload_reservation_repository
from src.schemas.storage import StorageItemCreate
from src.services.storage import StorageService
from src.services.storage_policy import object_prefixes, storage_policy


class UploadPolicyService:
    @staticmethod
    async def validate_svg(file):
        if file.filename and file.filename.lower().endswith(".svg"):
            content = await file.read(settings.MAX_UPLOAD_SIZE_BYTES + 1)
            text = content.decode("utf-8", errors="ignore")
            if re.search("<!ENTITY", text, re.IGNORECASE) or re.search(
                "<!DOCTYPE", text, re.IGNORECASE
            ):
                raise HTTPException(status_code=400, detail="Tệp đồ họa vector không an toàn")
            await file.seek(0)

    @staticmethod
    async def file_size(file):
        await file.seek(0)
        file.file.seek(0, 2)
        size = file.file.tell()
        await file.seek(0)
        UploadPolicyService.validate_size(size)
        return size

    @staticmethod
    def validate_size(size: int):
        if size < settings.MIN_FILE_SIZE_BYTES:
            raise HTTPException(status_code=400, detail="Tệp tải lên không được để trống")
        if size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="Tệp tải lên vượt quá kích thước cho phép")

    @staticmethod
    async def enforce_quota(user_id: str, additional_size: int):
        quota = await StorageService.get_storage_quota(user_id)
        if quota["used"] + additional_size > quota["limit"]:
            raise HTTPException(status_code=400, detail="Dung lượng lưu trữ đã đầy")

    @staticmethod
    async def register_item(result: dict, user_id: str, parent_id: str | None = None):
        return await StorageService.create_item(
            StorageItemCreate(
                name=result["filename"],
                is_folder=False,
                url=result["url"],
                size=result["size"],
                mime_type=result["content_type"],
                parent_id=parent_id,
            ),
            user_id,
        )

    @staticmethod
    async def can_download(file_path: str, user_id: str, is_system_admin: bool):
        if ".." in file_path or file_path.startswith("/"):
            return False
        policy = storage_policy()
        if file_path.startswith(policy["public_prefix"]):
            return True
        if file_path.startswith(object_prefixes(user_id)):
            return True
        if file_path.startswith(policy["temporary_prefix"].format(owner_id=user_id)):
            return True
        item = await storage_repository.find_one(
            {
                "url": file_path,
                "is_trashed": False,
                "$or": [{"owner_id": user_id}, {"shared_with.user_id": user_id}],
            },
            {"_id": 1},
        )
        return bool(item) or bool(
            is_system_admin and file_path.startswith(policy["system_prefix"])
        )

    @staticmethod
    async def reserve(file_path: str, reservation: dict):
        await upload_reservation_repository.reserve(
            file_path,
            int(storage_policy()["upload_reservation_ttl_seconds"]),
            reservation,
        )

    @staticmethod
    async def confirm_reservation(file_path: str, expected: dict):
        raw = await upload_reservation_repository.consume(file_path)
        if not raw:
            raise HTTPException(
                status_code=409, detail="Yêu cầu tải lên không tồn tại hoặc đã được xác nhận"
            )
        if json.loads(raw) != expected:
            raise HTTPException(status_code=400, detail="Thông tin xác nhận tải lên không hợp lệ")

    @staticmethod
    async def verify_stored_object(file_path: str, size: int, content_type: str):
        storage = await get_storage_client()
        try:
            metadata = await storage.head_object(Bucket=get_bucket(file_path), Key=file_path)
        except Exception as error:
            raise HTTPException(status_code=400, detail="Không tìm thấy tệp đã tải lên") from error
        actual_type = (metadata.get("ContentType") or "").split(";", 1)[0].lower()
        if metadata.get("ContentLength") != size or actual_type != content_type.lower():
            await storage.delete_object(Bucket=get_bucket(file_path), Key=file_path)
            raise HTTPException(status_code=400, detail="Nội dung tải lên không khớp yêu cầu")

    @staticmethod
    async def record_temporary_file(owner_id: str, file_path: str, filename: str):
        now = datetime.now(timezone.utc)
        await temporary_file_repository.insert(
            {
                "owner_id": owner_id,
                "url": file_path,
                "original_filename": filename,
                "created_at": now,
                "expires_at": now
                + timedelta(days=int(storage_policy()["temporary_file_retention_days"])),
            }
        )
