from typing import Any
from fastapi import APIRouter, Depends
from src.core.logging_route import LoggingRoute
from src.api.dependency import get_db, require_role
from src.schemas.cooperation import TransferOwnershipRequest, UpdateCollaboratorRoleRequest
from src.services.member import MemberService
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(route_class=LoggingRoute, prefix="/cong-tac")

MEMBER_ROLES = [Role.AUTHOR, Role.READER, Role.ADMIN]
OWNER_ROLES = [Role.AUTHOR, Role.ADMIN]

@router.get("/tai-lieu/{document_id}", response_model=APIResponse[Any])
async def get_collaborators(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await MemberService.get_collaborators(document_id, current_user),
        message="Trích xuất danh sách thành viên cộng tác hiện tại hoàn tất",
    )

@router.delete("/{collaboration_id}", response_model=APIResponse[Any])
async def remove_collaborator(
    collaboration_id: str,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await MemberService.remove_collaborator(collaboration_id, current_user),
        message="Thu hồi quyền truy cập và xóa thành viên cộng tác hoàn tất",
    )

@router.patch("/{collaboration_id}/vai-tro", response_model=APIResponse[Any])
async def update_collaborator_role(
    collaboration_id: str,
    data: UpdateCollaboratorRoleRequest,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await MemberService.update_collaborator_role(
            collaboration_id, data.role, current_user
        ),
        message="Cập nhật cấu hình phân quyền cộng tác viên hoàn tất",
    )

@router.post("/documents/{document_id}/transfer-ownership", response_model=APIResponse[Any])
async def transfer_ownership(
    document_id: str,
    data: TransferOwnershipRequest,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await MemberService.transfer_ownership(
            document_id, data.user_id, current_user
        ),
        message="Chuyển quyền sở hữu tài liệu cộng tác hoàn tất",
    )
