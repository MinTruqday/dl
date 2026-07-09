from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
import asyncio
from datetime import datetime, timezone

import httpx
from fastapi import Query
from src.schemas.thread import Record

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.repositories.message import MessageRepository
from src.repositories.conversation import ConversationRepository
from src.repositories.message import MessageRepository
from src.repositories.profile import ProfileRepository
from src.repositories.message import MessageRepository

class AttachmentService:
    @staticmethod
    @log_logic_execution
    async def share_document(receiver_id: str, document_id: str, current_user):
        doc = await MessageRepository.find_shared_document({"_id": document_id})
        if not doc:
            return None
        content = f"Shared document preview and link to access {doc.get('title')} at internal reference {document_id}"
        message = Record(
            sender_id=str(current_user.id),
            receiver_id=receiver_id,
            content=content,
            image_url=None,
            reply_to_id=None,
        )
        msg_dict = message.model_dump(by_alias=True)
        await MessageRepository.insert_one(msg_dict)
        await ThreadService._upsert_conversation(
            db,
            str(current_user.id),
            receiver_id,
            {
                "_id": msg_dict["_id"],
                "sender_id": str(current_user.id),
                "receiver_id": receiver_id,
                "content": content,
                "is_recalled": False,
                "created_at": msg_dict.get("created_at", datetime.now(timezone.utc)),
            },
        )
        return msg_dict

    @staticmethod
    @log_logic_execution
    async def get_shared_attachments(other_user_id: str, current_user) -> list:
        if other_user_id.startswith("group_"):
            query = {"receiver_id": other_user_id}
        else:
            query = {
                "$or": [
                    {"sender_id": str(current_user.id), "receiver_id": other_user_id},
                    {"sender_id": other_user_id, "receiver_id": str(current_user.id)},
                ]
            }
        query["is_recalled"] = False
        query["$or"] = [
            {"image_url": {"$ne": None, "$ne": ""}},
            {"content": {"$regex": "Shared document preview"}},
        ]
        messages = (
            await MessageRepository
            .find(query)
            .sort("created_at", -1)
            .execute()
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
            else:
                attachments.append(
                    {
                        "id": m["_id"],
                        "type": "document",
                        "content": m["content"],
                        "created_at": (
                            m["created_at"].isoformat()
                            if isinstance(m.get("created_at"), datetime)
                            else m.get("created_at")
                        ),
                    }
                )
        return attachments

