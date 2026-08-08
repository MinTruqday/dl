import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
from src.repositories.cooperation import CooperationRepository, DocumentRepository
from src.services.activity import ActivityService

class SnapshotService:
    @staticmethod
    @log_logic_execution
    async def create_draft_snapshot(
        document_id: str, version_name: str, current_user
    ) -> dict:
        doc = await DocumentRepository.find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        snapshot = {
            "_id": str(uuid.uuid4()),
            "document_id": document_id,
            "version_name": version_name,
            "created_by": str(current_user.id),
            "user_name": current_user.full_name,
            "file_url": doc.get("file_url"),
            "content": doc.get("description", ""),
            "timestamp": datetime.now(timezone.utc),
        }
        await CooperationRepository.insert_draft(snapshot)
        await ActivityService.log_activity(
            document_id,
            current_user.full_name,
            "Snapshot created",
            f"Created snapshot: {version_name}",
        )
        return {
            "id": snapshot["_id"],
            "version_name": version_name,
            "timestamp": snapshot["timestamp"].isoformat(),
            "message": "Tạo bản chụp nháp thành công",
        }

    @staticmethod
    @log_logic_execution
    async def get_draft_snapshots(document_id: str, current_user) -> list:
        doc = await DocumentRepository.find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        snapshots = (
            await mongo
            .find("collaboration_drafts", {"document_id": document_id})
            .sort("timestamp", -1)
            .to_list(length=50)
        )
        return [
            {
                "id": s["_id"],
                "version_name": s["version_name"],
                "user_name": s["user_name"],
                "file_url": s.get("file_url"),
                "timestamp": (
                    s["timestamp"].isoformat()
                    if isinstance(s.get("timestamp"), datetime)
                    else s.get("timestamp")
                ),
            }
            for s in snapshots
        ]
