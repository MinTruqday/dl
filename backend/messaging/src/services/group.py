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

class GroupService:
    @staticmethod
    @log_logic_execution
    async def create_group(group_name: str, member_ids: list, current_user):
        from uuid6 import uuid7

        group_id = f"group_{uuid7()}"
        members = list(set(member_ids + [str(current_user.id)]))
        group_doc = {
            "_id": group_id,
            "group_name": group_name,
            "created_by": str(current_user.id),
            "members": members,
            "created_at": datetime.now(timezone.utc),
        }
        await MessageRepository.insert_group(group_doc)
        return group_doc

