from src.core.infrastructure.redis import redis
import json
from typing import Any, List

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Query
from src.schemas.thread import Conversation, Creation, Response
from src.services.group import GroupService

from src.core.infrastructure.database import database
from src.core.dependency import AuthenticatedUser, Depends, Header, HTTPException
from src.core.dependency import get_current_user
from src.core.response import APIResponse
from src.repositories.message import MessageRepository

router = APIRouter(route_class=LoggingRoute, prefix="/tin-nhan")

@router.post("/nhom", response_model=APIResponse[Any])
async def create_group(req: dict, current_user=Depends(get_current_user)):
    group_name = req.get("group_name")
    member_ids = req.get("member_ids", [])
    if not group_name:
        return APIResponse(message="Tên nhóm cung cấp không hợp lệ", status=400)
    result = await GroupService.create_group(group_name, member_ids, current_user)
    return APIResponse(
        data=result, message="Tạo nhóm trò chuyện hoàn tất", status=201
    )

@router.post("/nhom/{group_id}/thanh-vien", response_model=APIResponse[Any])
async def add_member(group_id: str, req: dict, current_user=Depends(get_current_user)):
    user_id = req.get("user_id")
    if not user_id:
        return APIResponse(message="ID người dùng không hợp lệ", status=400)
    result = await GroupService.add_member(group_id, user_id, current_user)
    return APIResponse(data=result, message="Thêm thành viên hoàn tất")

@router.delete("/nhom/{group_id}/thanh-vien/{user_id}", response_model=APIResponse[Any])
async def remove_member(group_id: str, user_id: str, silent: bool = False, current_user=Depends(get_current_user)):
    result = await GroupService.remove_member(group_id, user_id, current_user, silent)
    return APIResponse(data=result, message="Xóa thành viên hoàn tất")

@router.put("/nhom/{group_id}/thong-tin", response_model=APIResponse[Any])
async def update_group_info(group_id: str, req: dict, current_user=Depends(get_current_user)):
    group_name = req.get("group_name")
    avatar_url = req.get("avatar_url")
    result = await GroupService.update_group_info(group_id, group_name, avatar_url, current_user)
    return APIResponse(data=result, message="Cập nhật thông tin nhóm hoàn tất")

@router.put("/nhom/{group_id}/quyen", response_model=APIResponse[Any])
async def set_deputy(group_id: str, req: dict, current_user=Depends(get_current_user)):
    user_id = req.get("user_id")
    action = req.get("action") # "promote" or "demote"
    if not user_id or action not in ["promote", "demote"]:
        return APIResponse(message="Dữ liệu không hợp lệ", status=400)
    
    if action == "promote":
        result = await GroupService.promote_deputy(group_id, user_id, current_user)
    else:
        result = await GroupService.demote_deputy(group_id, user_id, current_user)
    return APIResponse(data=result, message="Đã cập nhật quyền hoàn tất")

@router.put("/nhom/{group_id}/cai-dat", response_model=APIResponse[Any])
async def update_group_settings(group_id: str, req: dict, current_user=Depends(get_current_user)):
    result = await GroupService.update_group_settings(group_id, req, current_user)
    return APIResponse(data=result, message="Cập nhật cài đặt nhóm hoàn tất")

@router.post("/nhom/{group_id}/link", response_model=APIResponse[Any])
async def generate_invite_link(group_id: str, current_user=Depends(get_current_user)):
    result = await GroupService.generate_invite_link(group_id, current_user)
    return APIResponse(data=result, message="Đã tạo link mời mới")

@router.post("/nhom/tham-gia/{token}", response_model=APIResponse[Any])
async def join_by_link(token: str, current_user=Depends(get_current_user)):
    result = await GroupService.join_by_link(token, current_user)
    return APIResponse(data=result, message=result.get("message", ""))

@router.post("/nhom/{group_id}/duyet/{user_id}", response_model=APIResponse[Any])
async def review_join_request(group_id: str, user_id: str, req: dict, current_user=Depends(get_current_user)):
    action = req.get("action") # "approve" or "reject"
    if action == "approve":
        result = await GroupService.approve_join_request(group_id, user_id, current_user)
    elif action == "reject":
        result = await GroupService.reject_join_request(group_id, user_id, current_user)
    else:
        return APIResponse(message="Hành động không hợp lệ", status=400)
    return APIResponse(data=result, message=result.get("message", ""))

