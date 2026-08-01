from src.core.infrastructure.redis import redis
import json
from typing import Any, List

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Query
from src.schemas.thread import Conversation, Creation, Response
from src.services.attachment import AttachmentService

from src.core.infrastructure.database import database
from src.core.dependency import AuthenticatedUser, Depends, Header, HTTPException
from src.core.dependency import get_current_user, verify_internal_token
from src.core.response import APIResponse
from src.repositories.message import MessageRepository
from src.repositories.conversation import ConversationRepository
from src.api.thread import publish_personal_message

router = APIRouter(route_class=LoggingRoute, prefix="/tin-nhan")

@router.post(
    "/noi-bo/quyen-truy-cap-tep",
    dependencies=[Depends(verify_internal_token)],
)
async def can_access_file(req: dict):
    file_path = str(req.get("file_path", ""))
    user_id = str(req.get("user_id", ""))
    if not file_path or not user_id:
        raise HTTPException(status_code=400, detail="Thiếu thông tin tệp hoặc tài khoản")
    return {"allowed": await AttachmentService.can_access_file(file_path, user_id)}

@router.post(
    "/noi-bo/lien-he-duoc-phep",
    dependencies=[Depends(verify_internal_token)],
)
async def get_allowed_contacts(req: dict):
    user_id = str(req.get("user_id", ""))
    requested = {str(value) for value in req.get("requested", [])}
    cursor = ConversationRepository.find(
        {"$and": [{"participants": user_id}, {"participants": {"$in": list(requested)}}]},
        {"participants": 1},
    )
    allowed = set()
    async for conversation in cursor:
        allowed.update(set(map(str, conversation.get("participants", []))) & requested)
    return {"allowed": sorted(allowed - {user_id})}

@router.post(
    "/{receiver_id}/tai-lieu/chia-se",
    response_model=APIResponse[Any],
    status_code=201,
)
async def share_document(
    receiver_id: str, req: dict, current_user=Depends(get_current_user)
):
    document_id = req.get("document_id")
    if not document_id:
        raise HTTPException(
            status_code=400,
            detail="Yêu cầu chia sẻ không cung cấp đầy đủ mã định danh tài liệu",
        )
    result = await AttachmentService.share_document(receiver_id, document_id, current_user)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy tài liệu trong kho lưu trữ",
        )
    await publish_personal_message({"type": "new_message", "data": result}, receiver_id)
    return APIResponse(data=result, message="Chia sẻ tài liệu hoàn tất", status=201)

@router.get("/{other_user_id}/tai-lieu/da-chia-se", response_model=APIResponse[Any])
async def get_shared_attachments(
    other_user_id: str, current_user=Depends(get_current_user)
):
    return APIResponse(
        data=await AttachmentService.get_shared_attachments(other_user_id, current_user),
        message="Trích xuất danh sách tệp đính kèm hoàn tất",
    )
