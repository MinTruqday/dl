import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
from src.repositories.cooperation import CooperationRepository, DocumentRepository

class MemoService:
    @staticmethod
    @log_logic_execution
    async def send_memo(
        document_id: str, message: str, current_user
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
        memo = {
            "_id": str(uuid.uuid4()),
            "document_id": document_id,
            "sender_id": str(current_user.id),
            "sender_name": current_user.full_name,
            "message": message,
            "timestamp": datetime.now(timezone.utc),
        }
        await CooperationRepository.insert_memo(memo)
        return {
            "message": "Phân phối tin nhắn cộng tác nội bộ hoàn tất",
            "memo": memo,
        }

    @staticmethod
    @log_logic_execution
    async def get_memos(document_id: str, current_user) -> list:
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
        memos = (
            await mongo
            .find("collaboration_memos", {"document_id": document_id})
            .sort("timestamp", 1)
            .limit(100)
            .to_list(length=100)
        )
        return [
            {
                "id": m["_id"],
                "sender_id": m.get("sender_id") or m.get("user_id", ""),
                "sender_name": m.get("sender_name") or m.get("user_name", ""),
                "message": m["message"],
                "timestamp": (
                    m["timestamp"].isoformat()
                    if isinstance(m.get("timestamp"), datetime)
                    else m.get("timestamp")
                ),
            }
            for m in memos
        ]
