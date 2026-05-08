from core.database import db_client
from loguru import logger
from datetime import datetime, timezone
from fastapi import HTTPException
import uuid

class CoauthorService:
    @staticmethod
    async def invite_coauthor(document_id: str, target_user_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=403, detail="Bạn không có quyền mời đồng tác giả cho tài liệu này.")

        await db["notifications"].insert_one({
            "_id": str(uuid.uuid4()),
            "target_user_id": target_user_id,
            "title": "Lời mời đồng tác giả",
            "message": f"Bạn nhận được lời mời làm đồng tác giả cho tài liệu: {doc.get('title', document_id)}",
            "type": "coauthor_invite",
            "metadata": {"document_id": document_id, "inviter_id": str(current_user.id)},
            "is_read": False,
            "created_at": datetime.now(timezone.utc)
        })
        logger.info(f"Coauthor: User {current_user.id} invited {target_user_id} to document {document_id}")
        return {"message": "Đã gửi lời mời đồng tác giả thành công."}

    @staticmethod
    async def get_invites(current_user) -> list:
        db = db_client.mongodb.get_default_database()
        invites = await db["notifications"].find({
            "target_user_id": str(current_user.id),
            "type": "coauthor_invite"
        }).sort("created_at", -1).to_list(length=100)
        
        return [
            {
                "id": i["_id"],
                "document_id": i["metadata"].get("document_id"),
                "inviter_id": i["metadata"].get("inviter_id"),
                "message": i.get("message"),
                "created_at": i.get("created_at").isoformat() if i.get("created_at") else None,
                "read": i.get("is_read", False)
            }
            for i in invites
        ]

    @staticmethod
    async def accept_invite(notification_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        notif = await db["notifications"].find_one({
            "_id": notification_id,
            "target_user_id": str(current_user.id),
            "type": "coauthor_invite"
        })
        if not notif:
            raise HTTPException(status_code=404, detail="Không tìm thấy lời mời.")
        
        doc_id = notif["metadata"].get("document_id")
        await db["documents"].update_one(
            {"_id": doc_id},
            {"$addToSet": {"coauthors": str(current_user.id)}}
        )
        await db["notifications"].delete_one({"_id": notification_id})
        logger.info(f"Coauthor: User {current_user.id} accepted invite for document {doc_id}")
        return {"message": "Chúc mừng! Bạn đã trở thành đồng tác giả của tài liệu này."}

    @staticmethod
    async def reject_invite(notification_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        result = await db["notifications"].delete_one({
            "_id": notification_id,
            "target_user_id": str(current_user.id),
            "type": "coauthor_invite"
        })
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy lời mời để từ chối.")
        return {"message": "Đã từ chối lời mời cộng tác."}