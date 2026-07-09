from src.core.infrastructure.redis import redis
import json
from typing import Any, List

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Query
from src.schemas.thread import Conversation, Creation, Response
from src.services.attachment import AttachmentService

from src.core.infrastructure.database import database
from src.core.dependency import AuthenticatedUser, Depends, Header, HTTPException
from src.core.dependency import get_current_user
from src.core.response import APIResponse
from src.repositories.message import MessageRepository

router = APIRouter(route_class=LoggingRoute, prefix="/tin-nhan")

@router.post("/{receiver_id}/tai-lieu/chia-se", response_model=APIResponse[Any])
async def share_document(
    receiver_id: str, req: dict, current_user=Depends(get_current_user)
):
    document_id = req.get("document_id")
    if not document_id:
        return APIResponse(message="Yêu cầu chia sẻ không cung cấp đầy đủ mã định danh tài liệu", status=400)
    result = await AttachmentService.share_document(receiver_id, document_id, current_user)
    if not result:
        return APIResponse(
            message="Không tìm thấy tài liệu trong kho lưu trữ", status=404
        )
    await publish_personal_message({"type": "new_message", "data": result}, receiver_id)
    return APIResponse(data=result, message="Chia sẻ tài liệu thành công", status=201)

@router.get("/{other_user_id}/tai-lieu/da-chia-se", response_model=APIResponse[Any])
async def get_shared_attachments(
    other_user_id: str, current_user=Depends(get_current_user)
):
    return APIResponse(
        data=await AttachmentService.get_shared_attachments(other_user_id, current_user),
        message="Lấy danh sách tệp đính kèm thành công",
    )

