from typing import Any
from fastapi import APIRouter, Depends
from src.api.dependency import get_db, require_role
from src.schemas.cooperation import (
    CollaborationAccessRequestCreate,
    CollaborationAccessRequestReview,
)
from src.services.access_request import AccessRequestService
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(prefix="/cong-tac")

MEMBER_ROLES = [Role.AUTHOR, Role.READER, Role.ADMIN]
OWNER_ROLES = [Role.AUTHOR, Role.ADMIN]

@router.post("/tai-lieu/{document_id}/xin-quyen", response_model=APIResponse[Any], status_code=201)
async def create_access_request(
    document_id: str,
    data: CollaborationAccessRequestCreate,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await AccessRequestService.create_access_request(
            document_id, data.requested_role, data.message, current_user
        ),
        message="Gửi yêu cầu xin tham gia cộng tác hoàn tất",
        status=201,
    )

@router.get("/tai-lieu/{document_id}/yeu-cau-xin-quyen", response_model=APIResponse[Any])
async def get_document_access_requests(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await AccessRequestService.get_document_access_requests(
            document_id, current_user
        ),
        message="Trích xuất danh sách yêu cầu xin quyền hoàn tất",
    )

@router.get("/yeu-cau-xin-quyen-cua-toi", response_model=APIResponse[Any])
async def get_my_incoming_access_requests(
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await AccessRequestService.get_my_incoming_access_requests(current_user),
        message="Trích xuất danh sách yêu cầu xin quyền gửi tới tài liệu của bạn hoàn tất",
    )

@router.patch("/yeu-cau-xin-quyen/{request_id}", response_model=APIResponse[Any])
async def review_access_request(
    request_id: str,
    data: CollaborationAccessRequestReview,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await AccessRequestService.review_access_request(
            request_id, data.status, data.role, current_user
        ),
        message="Xử lý phản hồi yêu cầu xin quyền hoàn tất",
    )
