import asyncio
import json
import secrets
from datetime import datetime, timezone

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from uuid6 import uuid7

from src.core.infrastructure.redis import redis
from src.core.logic_logger import log_logic_execution
from src.repositories.message import MessageRepository
from src.repositories.profile import ProfileRepository
from src.schemas.thread import Record
from src.services.thread import ThreadService


class GroupService:
    @staticmethod
    def _is_manager(group: dict, user_id: str) -> bool:
        return user_id == group.get("created_by") or user_id in group.get("deputies", [])

    @staticmethod
    async def _get_group(group_id: str) -> dict:
        group = await MessageRepository.find_group({"_id": group_id})
        if not group:
            raise HTTPException(status_code=404, detail="Không tìm thấy nhóm trò chuyện")
        return group

    @staticmethod
    @log_logic_execution
    async def create_group(group_name: str, member_ids: list, current_user):
        clean_name = group_name.strip()
        if not clean_name or len(clean_name) > 100:
            raise HTTPException(status_code=400, detail="Tên nhóm không hợp lệ")
        creator_id = str(current_user.id)
        members = list(dict.fromkeys([creator_id, *[str(item) for item in member_ids]]))
        if len(members) > 100:
            raise HTTPException(status_code=400, detail="Nhóm vượt quá số thành viên cho phép")
        profiles = await asyncio.gather(
            *(ProfileRepository.get_profile(member_id) for member_id in members)
        )
        if any(profile is None for profile in profiles):
            raise HTTPException(status_code=400, detail="Danh sách thành viên chứa tài khoản không tồn tại")
        group_doc = {
            "_id": f"group_{uuid7()}",
            "group_name": clean_name,
            "created_by": creator_id,
            "deputies": [],
            "members": members,
            "messaging_restricted": False,
            "is_public": False,
            "requires_approval": False,
            "join_requests": [],
            "invite_token": secrets.token_urlsafe(24),
            "created_at": datetime.now(timezone.utc),
        }
        await MessageRepository.insert_group(group_doc)
        return group_doc

    @staticmethod
    @log_logic_execution
    async def add_member(group_id: str, new_user_id: str, current_user):
        group = await GroupService._get_group(group_id)
        user_id = str(current_user.id)
        if not GroupService._is_manager(group, user_id):
            raise HTTPException(status_code=403, detail="Bạn không có quyền thêm thành viên")
        if new_user_id in group.get("members", []):
            raise HTTPException(status_code=409, detail="Tài khoản đã ở trong nhóm")
        if len(group.get("members", [])) >= 100:
            raise HTTPException(status_code=400, detail="Nhóm đã đạt giới hạn thành viên")
        if not await ProfileRepository.get_profile(new_user_id):
            raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản cần thêm")
        await MessageRepository.update_group(
            {"_id": group_id},
            {"$addToSet": {"members": new_user_id}},
        )
        return {"success": True, "message": "Đã thêm thành viên"}

    @staticmethod
    @log_logic_execution
    async def remove_member(group_id: str, removed_user_id: str, current_user, silent: bool = False):
        group = await GroupService._get_group(group_id)
        user_id = str(current_user.id)
        if removed_user_id not in group.get("members", []):
            raise HTTPException(status_code=404, detail="Thành viên không còn ở trong nhóm")
        is_self = user_id == removed_user_id
        if removed_user_id == group.get("created_by"):
            raise HTTPException(status_code=400, detail="Chủ nhóm phải giải thể nhóm thay vì rời nhóm")
        if not is_self and not GroupService._is_manager(group, user_id):
            raise HTTPException(status_code=403, detail="Bạn không có quyền xóa thành viên")
        await MessageRepository.update_group(
            {"_id": group_id},
            {"$pull": {"members": removed_user_id, "deputies": removed_user_id}},
        )
        managers = [group.get("created_by"), *group.get("deputies", [])]
        visible_to = managers if silent else None
        record = Record(
            sender_id="system",
            receiver_id=group_id,
            content=f"{removed_user_id} đã rời nhóm",
            is_system=True,
            system_action="leave",
            visible_to=visible_to,
        ).model_dump(by_alias=True)
        await MessageRepository.insert_one(record)
        if not silent:
            await ThreadService._upsert_conversation("system", group_id, record)
        targets = [member for member in group.get("members", []) if member != removed_user_id]
        if silent:
            targets = [member for member in targets if member in managers]
        payload = json.dumps(jsonable_encoder({"type": "new_message", "data": record}))
        for target in targets:
            await redis.publish(f"message_delivery:{target}", payload)
        return {
            "success": True,
            "message": "Đã rời nhóm" if is_self else "Đã xóa thành viên khỏi nhóm",
        }

    @staticmethod
    @log_logic_execution
    async def update_group_info(group_id: str, group_name: str, avatar_url: str, current_user):
        group = await GroupService._get_group(group_id)
        if not GroupService._is_manager(group, str(current_user.id)):
            raise HTTPException(status_code=403, detail="Bạn không có quyền cập nhật nhóm")
        update = {}
        if group_name is not None:
            clean_name = group_name.strip()
            if not clean_name or len(clean_name) > 100:
                raise HTTPException(status_code=400, detail="Tên nhóm không hợp lệ")
            update["group_name"] = clean_name
        if avatar_url is not None:
            update["avatar_url"] = avatar_url
        if update:
            await MessageRepository.update_group({"_id": group_id}, {"$set": update})
        return {"success": True, "message": "Cập nhật thông tin nhóm thành công"}

    @staticmethod
    @log_logic_execution
    async def promote_deputy(group_id: str, promoted_user_id: str, current_user):
        group = await GroupService._get_group(group_id)
        if group.get("created_by") != str(current_user.id):
            raise HTTPException(status_code=403, detail="Chỉ chủ nhóm có quyền cấp phó nhóm")
        if promoted_user_id not in group.get("members", []):
            raise HTTPException(status_code=404, detail="Tài khoản không phải thành viên nhóm")
        if promoted_user_id == group.get("created_by"):
            raise HTTPException(status_code=400, detail="Chủ nhóm không thể trở thành phó nhóm")
        await MessageRepository.update_group(
            {"_id": group_id}, {"$addToSet": {"deputies": promoted_user_id}}
        )
        return {"success": True, "message": "Đã cấp quyền phó nhóm"}

    @staticmethod
    @log_logic_execution
    async def demote_deputy(group_id: str, demoted_user_id: str, current_user):
        group = await GroupService._get_group(group_id)
        if group.get("created_by") != str(current_user.id):
            raise HTTPException(status_code=403, detail="Chỉ chủ nhóm có quyền gỡ phó nhóm")
        await MessageRepository.update_group(
            {"_id": group_id}, {"$pull": {"deputies": demoted_user_id}}
        )
        return {"success": True, "message": "Đã gỡ quyền phó nhóm"}

    @staticmethod
    @log_logic_execution
    async def update_group_settings(group_id: str, group_settings: dict, current_user):
        group = await GroupService._get_group(group_id)
        if not GroupService._is_manager(group, str(current_user.id)):
            raise HTTPException(status_code=403, detail="Bạn không có quyền cập nhật cài đặt nhóm")
        allowed = {"messaging_restricted", "is_public", "requires_approval"}
        update = {
            key: value
            for key, value in group_settings.items()
            if key in allowed and isinstance(value, bool)
        }
        if update:
            await MessageRepository.update_group({"_id": group_id}, {"$set": update})
        return {"success": True, "message": "Cập nhật cài đặt nhóm thành công"}

    @staticmethod
    @log_logic_execution
    async def generate_invite_link(group_id: str, current_user):
        group = await GroupService._get_group(group_id)
        if not GroupService._is_manager(group, str(current_user.id)):
            raise HTTPException(status_code=403, detail="Bạn không có quyền tạo liên kết mời")
        token = secrets.token_urlsafe(24)
        await MessageRepository.update_group(
            {"_id": group_id}, {"$set": {"invite_token": token}}
        )
        return {"success": True, "invite_token": token}

    @staticmethod
    @log_logic_execution
    async def join_by_link(token: str, current_user):
        group = await MessageRepository.find_group({"invite_token": token})
        if not group:
            raise HTTPException(status_code=404, detail="Liên kết mời không hợp lệ")
        user_id = str(current_user.id)
        if user_id in group.get("members", []):
            raise HTTPException(status_code=409, detail="Tài khoản đã ở trong nhóm")
        if len(group.get("members", [])) >= 100:
            raise HTTPException(status_code=400, detail="Nhóm đã đạt giới hạn thành viên")
        if group.get("requires_approval"):
            result = await MessageRepository.update_group(
                {"_id": group["_id"], "join_requests": {"$ne": user_id}},
                {"$addToSet": {"join_requests": user_id}},
            )
            if result.modified_count == 0:
                raise HTTPException(status_code=409, detail="Yêu cầu tham gia đã được gửi")
            return {"success": True, "status": "pending", "message": "Đã gửi yêu cầu tham gia nhóm"}
        await MessageRepository.update_group(
            {"_id": group["_id"]}, {"$addToSet": {"members": user_id}}
        )
        return {
            "success": True,
            "status": "joined",
            "message": "Đã tham gia nhóm",
            "group_id": group["_id"],
        }

    @staticmethod
    async def _review_join_request(group_id: str, reviewed_user_id: str, current_user, approve: bool):
        group = await GroupService._get_group(group_id)
        if not GroupService._is_manager(group, str(current_user.id)):
            raise HTTPException(status_code=403, detail="Bạn không có quyền duyệt thành viên")
        if reviewed_user_id not in group.get("join_requests", []):
            raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu tham gia")
        update = {"$pull": {"join_requests": reviewed_user_id}}
        if approve:
            update["$addToSet"] = {"members": reviewed_user_id}
        await MessageRepository.update_group({"_id": group_id}, update)
        return {
            "success": True,
            "message": "Đã duyệt thành viên" if approve else "Đã từ chối yêu cầu tham gia",
        }

    @staticmethod
    @log_logic_execution
    async def approve_join_request(group_id: str, user_id: str, current_user):
        return await GroupService._review_join_request(group_id, user_id, current_user, True)

    @staticmethod
    @log_logic_execution
    async def reject_join_request(group_id: str, user_id: str, current_user):
        return await GroupService._review_join_request(group_id, user_id, current_user, False)
