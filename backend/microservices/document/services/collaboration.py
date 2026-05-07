from core.database import db_client
from fastapi import HTTPException
from datetime import datetime
import uuid
from loguru import logger
class CollaborationService:
    @staticmethod
    async def send_collaboration_invite(document_id: str, invitee_email: str, role: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại hoặc bạn không có quyền truy cập.")
        invitee = await db["users"].find_one({"email": invitee_email})
        if not invitee:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng với email này.")
        invitee_id = str(invitee["_id"])
        if invitee_id == str(current_user.id):
            raise HTTPException(status_code=400, detail="Bạn không thể tự mời chính mình cộng tác.")
        existing_invite = await db["collaboration_invites"].find_one({
            "document_id": document_id,
            "invitee_id": invitee_id,
            "status": "PENDING"
        })
        if existing_invite:
            raise HTTPException(status_code=400, detail="Đã có một lời mời đang chờ người này xác nhận.")
        coauthors = doc.get("coauthors", [])
        if invitee_id in coauthors:
            raise HTTPException(status_code=400, detail="Người này đã là cộng tác viên của tài liệu.")
        invite = {
            "_id": str(uuid.uuid4()),
            "document_id": document_id,
            "document_title": doc.get("title", "Tài liệu không tên"),
            "inviter_id": str(current_user.id),
            "inviter_name": current_user.full_name,
            "invitee_id": invitee_id,
            "role": role,
            "status": "PENDING",
            "created_at": datetime.utcnow()
        }
        await db["collaboration_invites"].insert_one(invite)
        logger.info(f"Workspace: User {current_user.id} invited {invitee_id} to collaborate on {document_id}")
        return {"message": "Đã gửi lời mời cộng tác thành công.", "invite_id": invite["_id"]}
    @staticmethod
    async def get_my_collaboration_invites(current_user) -> list:
        db = db_client.mongodb.get_default_database()
        invites = await db["collaboration_invites"].find(
            {"invitee_id": str(current_user.id), "status": "PENDING"}
        ).sort("created_at", -1).to_list(length=100)
        return invites
    @staticmethod
    async def respond_to_collaboration_invite(invite_id: str, status: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        invite = await db["collaboration_invites"].find_one({
            "_id": invite_id,
            "invitee_id": str(current_user.id),
            "status": "PENDING"
        })
        if not invite:
            raise HTTPException(status_code=404, detail="Lời mời không tồn tại hoặc đã được xử lý.")
        if status not in ["ACCEPTED", "REJECTED"]:
            raise HTTPException(status_code=400, detail="Trạng thái phản hồi không hợp lệ.")
        await db["collaboration_invites"].update_one(
            {"_id": invite_id},
            {"$set": {"status": status, "responded_at": datetime.utcnow()}}
        )
        if status == "ACCEPTED":
            await db["documents"].update_one(
                {"_id": invite["document_id"]},
                {"$push": {"coauthors": str(current_user.id)}, "$set": {"updated_at": datetime.utcnow()}}
            )
        logger.info(f"Workspace: User {current_user.id} {status} collaboration invite {invite_id}")
        return {"message": f"Đã { 'chấp nhận' if status == 'ACCEPTED' else 'từ chối' } lời mời cộng tác."}
