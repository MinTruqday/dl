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

    @staticmethod
    @log_logic_execution
    async def add_member(group_id: str, new_user_id: str, current_user):
        group = await MessageRepository.find_group({"_id": group_id})
        if not group:
            raise ValueError("Group not found")
        if str(current_user.id) not in group.get("members", []):
            raise ValueError("User is not a member of this group")
        if new_user_id in group.get("members", []):
            raise ValueError("User is already in the group")
        
        await MessageRepository.update_group(
            {"_id": group_id},
            {"$push": {"members": new_user_id}}
        )
        return {"success": True, "message": "Đã thêm thành viên"}

    @staticmethod
    @log_logic_execution
    async def remove_member(group_id: str, user_id: str, current_user):
        group = await MessageRepository.find_group({"_id": group_id})
        if not group:
            raise ValueError("Group not found")
        
        is_admin = group.get("created_by") == str(current_user.id)
        if str(current_user.id) != user_id and not is_admin:
            raise ValueError("User lacks permission to remove this member")
        
        await MessageRepository.update_group(
            {"_id": group_id},
            {"$pull": {"members": user_id}}
        )
        return {"success": True, "message": "Đã xóa thành viên khỏi nhóm"}

    @staticmethod
    @log_logic_execution
    async def update_group_info(group_id: str, group_name: str, avatar_url: str, current_user):
        group = await MessageRepository.find_group({"_id": group_id})
        if not group:
            raise ValueError("Group not found")
        if str(current_user.id) not in group.get("members", []):
            raise ValueError("User lacks permission to update this group")
        
        update_data = {}
        if group_name:
            update_data["group_name"] = group_name
        if avatar_url is not None:
            update_data["avatar_url"] = avatar_url
            
        if update_data:
            await MessageRepository.update_group(
                {"_id": group_id},
                {"$set": update_data}
            )
        return {"success": True, "message": "Cập nhật thông tin nhóm thành công"}
