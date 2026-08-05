from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from src.core.dependency import CurrentUser, Role, get_current_user, get_db, require_role
from src.core.logging_route import LoggingRoute
from src.core.response import APIResponse
from src.services.audit import AuditService

router = APIRouter(route_class=LoggingRoute, prefix="/kiem-toan")


@router.get(
    "/nhat-ky",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_audit_records(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    module: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    action: Optional[str] = Query(default=None),
    actor_id: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    from_date: Optional[str] = Query(default=None),
    to_date: Optional[str] = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    data = await AuditService.get_audit_logs(
        page=page,
        page_size=page_size,
        module=module,
        severity=severity,
        status=status,
        action=action,
        actor_id=actor_id,
        search=search,
        from_date=from_date,
        to_date=to_date,
    )
    return APIResponse(
        data=data,
        message="Trích xuất danh sách nhật ký kiểm toán thành công",
    )


@router.get(
    "/logs",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_logs_legacy(
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await AuditService.get_moderator_activity_log(str(current_user.id)),
        message="Trích xuất nhật ký hoạt động hoàn tất",
    )


@router.get(
    "/thong-ke",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_audit_statistics(
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    data = await AuditService.get_audit_stats()
    return APIResponse(
        data=data,
        message="Trích xuất dữ liệu thống kê kiểm toán thành công",
    )


@router.get(
    "/ket-xuat",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def export_audit_records(
    format: str = Query(default="json"),
    module: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    action: Optional[str] = Query(default=None),
    actor_id: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    from_date: Optional[str] = Query(default=None),
    to_date: Optional[str] = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    data = await AuditService.export_audit_logs(
        format_type=format,
        module=module,
        severity=severity,
        status=status,
        action=action,
        actor_id=actor_id,
        search=search,
        from_date=from_date,
        to_date=to_date,
    )
    return APIResponse(
        data=data,
        message="Kết xuất dữ liệu kiểm toán thành công",
    )


@router.get(
    "/kiem-tra-toan-ven",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def verify_integrity(
    log_id: Optional[str] = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    data = await AuditService.verify_audit_integrity(log_id=log_id)
    return APIResponse(
        data=data,
        message="Kiểm tra tính toàn vẹn dữ liệu kiểm toán hoàn tất",
    )
