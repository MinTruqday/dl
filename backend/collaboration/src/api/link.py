from typing import Any
from fastapi import APIRouter, Depends
from src.core.logging_route import LoggingRoute
from src.api.dependency import get_db, require_role
from src.schemas.cooperation import CollaborationShareLinkConfig, CollaborationShareLinkJoin
from src.services.link import LinkService
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(route_class=LoggingRoute, prefix="/cong-tac")

MEMBER_ROLES = [Role.AUTHOR, Role.READER, Role.ADMIN]
OWNER_ROLES = [Role.AUTHOR, Role.ADMIN]

@router.post("/tai-lieu/{document_id}/ma-moi", response_model=APIResponse[Any])
async def generate_invite_code(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await LinkService.generate_invite_code(document_id, current_user),
        message="Khởi tạo mã mời tham gia cộng tác hoàn tất",
    )

@router.post("/tham-gia/{invite_code}", response_model=APIResponse[Any])
async def join_via_invite_code(
    invite_code: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await LinkService.join_via_invite_code(invite_code, current_user),
        message="Tham gia không gian cộng tác tài liệu hoàn tất",
    )

@router.post("/tai-lieu/{document_id}/lien-ket-chia-se", response_model=APIResponse[Any])
async def configure_share_link(
    document_id: str,
    data: CollaborationShareLinkConfig,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await LinkService.configure_share_link(
            document_id,
            data.is_active,
            data.password,
            data.default_role,
            data.expires_in_hours,
            current_user,
        ),
        message="Cấu hình liên kết chia sẻ cộng tác hoàn tất",
    )

@router.get("/tai-lieu/{document_id}/lien-ket-chia-se", response_model=APIResponse[Any])
async def get_share_link_config(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await LinkService.get_share_link_config(document_id, current_user),
        message="Trích xuất thông tin cấu hình liên kết chia sẻ hoàn tất",
    )

@router.get("/thong-tin-lien-ket/{share_token}", response_model=APIResponse[Any])
async def get_public_share_link_info(
    share_token: str,
    db=Depends(get_db),
):
    return APIResponse(
        data=await LinkService.get_public_share_link_info(share_token),
        message="Trích xuất thông tin phòng cộng tác liên kết hoàn tất",
    )

@router.post("/tham-gia-lien-ket/{share_token}", response_model=APIResponse[Any])
async def join_via_share_link(
    share_token: str,
    data: CollaborationShareLinkJoin,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await LinkService.join_via_share_link(
            share_token, data.password, current_user
        ),
        message="Xử lý gia nhập không gian cộng tác hoàn tất",
    )
