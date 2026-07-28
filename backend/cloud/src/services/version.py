from fastapi import HTTPException

from src.core.logic_logger import log_logic_execution
from src.services.storage import StorageService


class VersionService:
    @staticmethod
    @log_logic_execution
    async def create_file_version(
        file_id: str,
        owner_id: str,
        new_url: str,
        new_size: int,
    ) -> dict:
        item = await StorageService.add_version(
            file_id,
            owner_id,
            new_url,
            new_size,
        )
        return {
            "status": "success",
            "file_id": file_id,
            "version_count": len(item.versions),
        }

    @staticmethod
    @log_logic_execution
    async def get_file_versions(file_id: str, owner_id: str) -> list:
        item = await StorageService.get_item(file_id, owner_id)
        if not item or item.is_folder:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tệp tin",
            )
        return [version.model_dump() for version in reversed(item.versions)]

    @staticmethod
    @log_logic_execution
    async def restore_file_version(
        file_id: str,
        version_id: str,
        owner_id: str,
    ) -> dict:
        item = await StorageService.get_item(file_id, owner_id)
        if not item or item.is_folder:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tệp tin",
            )
        version = next(
            (
                candidate
                for candidate in item.versions
                if candidate.version_id == version_id
            ),
            None,
        )
        if not version:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy phiên bản tệp tin",
            )
        restored = await StorageService.add_version(
            file_id,
            owner_id,
            version.url,
            version.size,
        )
        return {
            "status": "success",
            "file_id": file_id,
            "restored_version_id": version_id,
            "version_count": len(restored.versions),
        }
