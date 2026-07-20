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

        import secrets
        group_id = f"group_{uuid7()}"
        members = list(set(member_ids + [str(current_user.id)]))
        group_doc = {
            "_id": group_id,
            "group_name": group_name,
            "created_by": str(current_user.id),
            "deputies": [],
            "members": members,
            "messaging_restricted": False,
            "is_public": False,
            "requires_approval": False,
            "join_requests": [],
            "invite_token": secrets.token_urlsafe(16),
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
    async def remove_member(group_id: str, user_id: str, current_user, silent: bool = False):
        group = await MessageRepository.find_group({"_id": group_id})
        if not group:
            raise ValueError("Group not found")
        
        is_admin = group.get("created_by") == str(current_user.id)
        is_deputy = str(current_user.id) in group.get("deputies", [])
        is_self = str(current_user.id) == user_id

        if not is_self and not is_admin and not is_deputy:
            raise ValueError("User lacks permission to remove this member")
        
        await MessageRepository.update_group(
            {"_id": group_id},
            {"$pull": {"members": user_id, "deputies": user_id}}
        )
        
        from src.schemas.thread import Record
        import json
        from src.core.infrastructure.mq import mq
        
        admins = [group.get("created_by")] + group.get("deputies", [])
        visible_to = admins if silent else None
        
        system_msg = {
            "sender_id": "system",
            "receiver_id": group_id,
            "content": f"{user_id} đã rời nhóm",
            "is_system": True,
            "system_action": "leave",
            "visible_to": visible_to
        }
        record = Record(**system_msg).model_dump(by_alias=True)
        await MessageRepository.insert_one(record)
        
        for member in group.get("members", []):
            if member == user_id: continue
            if silent and member not in admins: continue
            await mq.publish("messaging_queue", {"action": "message_delivery", "receiver_id": member, "data": json.dumps({"type": "new_message", "data": record})})

        return {"success": True, "message": "Đã rời nhóm" if is_self else "Đã xóa thành viên khỏi nhóm"}

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

    @staticmethod
    @log_logic_execution
    async def promote_deputy(group_id: str, user_id: str, current_user):
        group = await MessageRepository.find_group({"_id": group_id})
        if not group: raise ValueError("Group not found")
        if group.get("created_by") != str(current_user.id):
            raise ValueError("Only group admin has permission to do this")
        if user_id not in group.get("members", []):
            raise ValueError("User is not a member of this group")
        
        await MessageRepository.update_group(
            {"_id": group_id},
            {"$addToSet": {"deputies": user_id}}
        )
        return {"success": True, "message": "Đã thăng cấp phó nhóm"}

    @staticmethod
    @log_logic_execution
    async def demote_deputy(group_id: str, user_id: str, current_user):
        group = await MessageRepository.find_group({"_id": group_id})
        if not group: raise ValueError("Group not found")
        if group.get("created_by") != str(current_user.id):
            raise ValueError("Only group admin has permission to do this")
        
        await MessageRepository.update_group(
            {"_id": group_id},
            {"$pull": {"deputies": user_id}}
        )
        return {"success": True, "message": "Đã giáng cấp phó nhóm"}

    @staticmethod
    @log_logic_execution
    async def update_group_settings(group_id: str, settings: dict, current_user):
        group = await MessageRepository.find_group({"_id": group_id})
        if not group: raise ValueError("Group not found")
        is_admin = group.get("created_by") == str(current_user.id)
        is_deputy = str(current_user.id) in group.get("deputies", [])
        if not is_admin and not is_deputy:
            raise ValueError("User lacks permission to update settings")
        
        allowed_keys = ["messaging_restricted", "is_public", "requires_approval"]
        update_data = {k: v for k, v in settings.items() if k in allowed_keys}
        
        if update_data:
            await MessageRepository.update_group(
                {"_id": group_id},
                {"$set": update_data}
            )
        return {"success": True, "message": "Cập nhật cài đặt thành công"}

    @staticmethod
    @log_logic_execution
    async def generate_invite_link(group_id: str, current_user):
        import secrets
        group = await MessageRepository.find_group({"_id": group_id})
        if not group: raise ValueError("Group not found")
        is_admin = group.get("created_by") == str(current_user.id)
        is_deputy = str(current_user.id) in group.get("deputies", [])
        if not is_admin and not is_deputy:
            raise ValueError("User lacks permission")
        
        new_token = secrets.token_urlsafe(16)
        await MessageRepository.update_group(
            {"_id": group_id},
            {"$set": {"invite_token": new_token}}
        )
        return {"success": True, "invite_token": new_token}

    @staticmethod
    @log_logic_execution
    async def join_by_link(token: str, current_user):
        group = await MessageRepository.find_group({"invite_token": token})
        if not group:
            raise ValueError("Invalid or expired invite link")
            
        group_id = group["_id"]
        user_id = str(current_user.id)
        
        if user_id in group.get("members", []):
            raise ValueError("User is already in this group")
            
        if group.get("requires_approval"):
            if user_id in group.get("join_requests", []):
                raise ValueError("User has already submitted a join request")
            await MessageRepository.update_group(
                {"_id": group_id},
                {"$addToSet": {"join_requests": user_id}}
            )
            return {"success": True, "status": "pending", "message": "Đã gửi yêu cầu tham gia nhóm"}
            
        await MessageRepository.update_group(
            {"_id": group_id},
            {"$addToSet": {"members": user_id}}
        )
        return {"success": True, "status": "joined", "message": "Đã tham gia nhóm", "group_id": group_id}

    @staticmethod
    @log_logic_execution
    async def approve_join_request(group_id: str, user_id: str, current_user):
        group = await MessageRepository.find_group({"_id": group_id})
        if not group: raise ValueError("Group not found")
        is_admin = group.get("created_by") == str(current_user.id)
        is_deputy = str(current_user.id) in group.get("deputies", [])
        if not is_admin and not is_deputy:
            raise ValueError("User lacks permission")
            
        if user_id not in group.get("join_requests", []):
            raise ValueError("User has not submitted a join request")
            
        await MessageRepository.update_group(
            {"_id": group_id},
            {
                "$pull": {"join_requests": user_id},
                "$addToSet": {"members": user_id}
            }
        )
        return {"success": True, "message": "Đã duyệt thành viên"}

    @staticmethod
    @log_logic_execution
    async def reject_join_request(group_id: str, user_id: str, current_user):
        group = await MessageRepository.find_group({"_id": group_id})
        if not group: raise ValueError("Group not found")
        is_admin = group.get("created_by") == str(current_user.id)
        is_deputy = str(current_user.id) in group.get("deputies", [])
        if not is_admin and not is_deputy:
            raise ValueError("User lacks permission")
            
        await MessageRepository.update_group(
            {"_id": group_id},
            {"$pull": {"join_requests": user_id}}
        )
        return {"success": True, "message": "Đã từ chối yêu cầu tham gia"}
