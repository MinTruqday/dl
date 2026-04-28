from core.database import db_client
from loguru import logger
from datetime import datetime
from fastapi import HTTPException
import uuid

class CoauthorService:
    @staticmethod
    async def invite_coauthor(document_id: str, target_user_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc:
            logger.warning(f"User {current_user.id} unauthorized coauthor invitation attempt for document {document_id}")
            raise HTTPException(status_code=403, detail="Bạn không có quyền mời đồng tác giả cho tài liệu này.")

        await db["notifications"].insert_one({
            "_id": str(uuid.uuid4()),
            "user_id": target_user_id,
            "title": "Lời mời đồng tác giả",
            "message": f"Bạn nhận được lời mời làm đồng tác giả cho tài liệu: {doc.get('title', document_id)}",
            "type": "coauthor_invite",
            "metadata": {"document_id": document_id, "inviter_id": str(current_user.id)},
            "read": False,
            "created_at": datetime.utcnow()
        })
        logger.info(f"Coauthor invitation sent from {current_user.id} to {target_user_id} for document {document_id}")
        return {"message": "Đã gửi lời mời đồng tác giả thành công."}