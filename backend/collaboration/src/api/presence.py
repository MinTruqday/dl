from typing import Any
from fastapi import APIRouter, Depends
from src.api.dependency import get_db, require_role
from src.schemas.cooperation import (
    CollaborationModeUpdate,
    CollaborationScheduleUpdate,
    UpdateCollabAccessRequest,
)
from src.services.presence import PresenceService
from src.services.cooperation import CooperationService
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(prefix="/cong-tac")

MEMBER_ROLES = [Role.AUTHOR, Role.READER, Role.ADMIN]
OWNER_ROLES = [Role.AUTHOR, Role.ADMIN]

@router.post("/tai-lieu/{document_id}/ping", response_model=APIResponse[Any])
async def ping_status(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PresenceService.update_status(document_id, current_user),
        message="Đồng bộ hóa trạng thái hoạt động trực tuyến hoàn tất",
    )

@router.get("/tai-lieu/{document_id}/truc-tuyen", response_model=APIResponse[Any])
async def get_online_collaborators(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PresenceService.get_online_collaborators(document_id),
        message="Trích xuất danh sách cộng tác viên đang trực tuyến hoàn tất",
    )

@router.patch("/tai-lieu/{document_id}/quyen-truy-cap", response_model=APIResponse[Any])
async def update_collab_access(
    document_id: str,
    data: UpdateCollabAccessRequest,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CooperationService.update_collab_access(
            document_id, data.access_level, current_user
        ),
        message="Cập nhật cấu hình mức độ quyền truy cập cộng tác hoàn tất",
    )

@router.post("/tai-lieu/{document_id}/che-do-truy-cap", response_model=APIResponse[Any])
async def update_collaboration_mode(
    document_id: str,
    data: CollaborationModeUpdate,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PresenceService.update_collaboration_mode(
            document_id, data.collaboration_mode, current_user
        ),
        message="Cập nhật chế độ đóng mở tài liệu hoàn tất",
    )

@router.get("/tai-lieu/{document_id}/che-do-truy-cap", response_model=APIResponse[Any])
async def get_collaboration_mode(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PresenceService.get_collaboration_mode(document_id, current_user),
        message="Trích xuất thông tin chế độ đóng mở tài liệu hoàn tất",
    )

@router.post("/tai-lieu/{document_id}/lich-hen-gio", response_model=APIResponse[Any])
async def update_collaboration_schedules(
    document_id: str,
    data: CollaborationScheduleUpdate,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PresenceService.update_collaboration_schedules(
            document_id, [s.model_dump() for s in data.schedules], current_user
        ),
        message="Cập nhật lịch hẹn giờ quyền hạn cộng tác hoàn tất",
    )

@router.get("/tai-lieu/{document_id}/lich-hen-gio", response_model=APIResponse[Any])
async def get_collaboration_schedules(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PresenceService.get_collaboration_schedules(document_id, current_user),
        message="Trích xuất danh sách lịch hẹn giờ cộng tác hoàn tất",
    )
