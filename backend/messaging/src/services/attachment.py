from datetime import datetime

from fastapi import HTTPException

from src.core.logic_logger import log_logic_execution
from src.repositories.message import MessageRepository
from src.services.thread import ThreadService

class AttachmentService:
    @staticmethod
    async def can_access_file(file_path: str, user_id: str) -> bool:
        groups = await MessageRepository.find_groups(
            {"members": user_id}, {"_id": 1}
        ).to_list(length=None)
        group_ids = [str(group["_id"]) for group in groups]
        message = await MessageRepository.find_one(
            {
                "$and": [
                    {
                        "$or": [
                            {"image_url": file_path},
                            {"audio_url": file_path},
                            {"attachments.url": file_path},
                            {"attachments.file_url": file_path},
                        ]
                    },
                    {
                        "$or": [
                            {"sender_id": user_id},
                            {"receiver_id": user_id},
                            {"receiver_id": {"$in": group_ids}},
                        ]
                    },
                ]
            },
            {"_id": 1},
        )
        return message is not None

    @staticmethod
    @log_logic_execution
    async def share_document(receiver_id: str, document_id: str, current_user):
        doc = await MessageRepository.find_shared_document({"_id": document_id})
        if not doc:
            return None
        user_id = str(current_user.id)
        can_share = (
            doc.get("creator_id") == user_id
            or user_id in doc.get("coauthors", [])
            or (
                doc.get("status") == "published"
                and doc.get("visibility", "public") == "public"
                and not doc.get("is_deleted", False)
            )
        )
        if not can_share:
            raise HTTPException(status_code=403, detail="Bạn không có quyền chia sẻ tài liệu này")
        content = f"Shared document preview and link to access {doc.get('title')} at internal reference {document_id}"
        return await ThreadService.send_message(
            receiver_id=receiver_id,
            content=content,
            current_user=current_user,
            attachments=[
                {
                    "type": "document",
                    "document_id": document_id,
                    "title": doc.get("title"),
                    "cover_url": doc.get("cover_url"),
                }
            ],
        )

    @staticmethod
    @log_logic_execution
    async def get_shared_attachments(other_user_id: str, current_user) -> list:
        if other_user_id.startswith("group_"):
            await ThreadService.ensure_group_access(other_user_id, str(current_user.id))
            query = {"receiver_id": other_user_id}
        else:
            query = {
                "$or": [
                    {"sender_id": str(current_user.id), "receiver_id": other_user_id},
                    {"sender_id": other_user_id, "receiver_id": str(current_user.id)},
                ]
            }
        query["is_recalled"] = False
        query["is_scheduled"] = {"$ne": True}
        query["deleted_by"] = {"$ne": str(current_user.id)}
        query["$and"] = [
            {
                "$or": [
                    {"image_url": {"$exists": True, "$nin": [None, ""]}},
                    {"attachments.0": {"$exists": True}},
                ]
            },
            {"$or": [{"visible_to": None}, {"visible_to": str(current_user.id)}]},
        ]
        messages = (
            await MessageRepository
            .find(query)
            .sort("created_at", -1)
            .to_list(length=None)
        )
        attachments = []
        for m in messages:
            if m.get("image_url"):
                attachments.append(
                    {
                        "id": m["_id"],
                        "type": "image",
                        "url": m["image_url"],
                        "created_at": (
                            m["created_at"].isoformat()
                            if isinstance(m.get("created_at"), datetime)
                            else m.get("created_at")
                        ),
                    }
                )
            for item in m.get("attachments", []):
                attachments.append(
                    {
                        "id": m["_id"],
                        **item,
                        "created_at": (
                            m["created_at"].isoformat()
                            if isinstance(m.get("created_at"), datetime)
                            else m.get("created_at")
                        ),
                    }
                )
        return attachments
