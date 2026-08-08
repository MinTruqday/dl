from typing import Any
from fastapi import APIRouter, Depends
from src.core.logging_route import LoggingRoute
from src.api.dependency import get_db, require_role
from src.schemas.cooperation import CreateDraftSnapshotRequest
from src.services.snapshot import SnapshotService
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(route_class=LoggingRoute, prefix="/cong-tac")

MEMBER_ROLES = [Role.AUTHOR, Role.READER, Role.ADMIN]

@router.post(
    "/tai-lieu/{document_id}/phien-ban",
    response_model=APIResponse[Any],
    status_code=201,
)
async def create_snapshot(
    document_id: str,
    data: CreateDraftSnapshotRequest,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await SnapshotService.create_draft_snapshot(
            document_id, data.version_name, current_user
        ),
        message="Lưu trữ bản chụp phiên bản tài liệu hoàn tất",
        status=201,
    )

@router.get("/tai-lieu/{document_id}/phien-ban", response_model=APIResponse[Any])
async def get_snapshots(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await SnapshotService.get_draft_snapshots(document_id, current_user),
        message="Trích xuất danh sách bản chụp phiên bản tài liệu hoàn tất",
    )
