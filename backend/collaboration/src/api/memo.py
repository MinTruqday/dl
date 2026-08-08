from typing import Any
from fastapi import APIRouter, Depends
from src.core.logging_route import LoggingRoute
from src.api.dependency import get_db, require_role
from src.schemas.cooperation import CollabMemoCreateRequest
from src.services.memo import MemoService
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(route_class=LoggingRoute, prefix="/cong-tac")

MEMBER_ROLES = [Role.AUTHOR, Role.READER, Role.ADMIN]

@router.post("/tai-lieu/{document_id}/tin-nhan", response_model=APIResponse[Any])
async def send_memo(
    document_id: str,
    data: CollabMemoCreateRequest,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await MemoService.send_memo(
            document_id, data.message, current_user
        ),
        message="Phân phối tin nhắn cộng tác nội bộ hoàn tất",
    )

@router.get("/tai-lieu/{document_id}/tin-nhan", response_model=APIResponse[Any])
async def get_memos(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await MemoService.get_memos(document_id, current_user),
        message="Trích xuất nhật ký tin nhắn cộng tác nội bộ hoàn tất",
    )
