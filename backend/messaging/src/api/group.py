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
        data=result, message="Tạo nhóm trò chuyện thành công", status=201
    )

