from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from src.core.dependency import CurrentUser, Role, get_current_user, get_db, require_role
from src.core.logging_route import LoggingRoute
from src.core.response import APIResponse
from src.services.analytics import AnalyticsService

router = APIRouter(route_class=LoggingRoute, prefix="/phan-tich")


@router.get(
    "/tong-quan",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER]))],
)
async def get_overview(
    from_date: Optional[str] = Query(default=None),
    to_date: Optional[str] = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    data = await AnalyticsService.get_author_overview(
        user_id=str(current_user.id),
        from_date=from_date,
        to_date=to_date,
    )
    return APIResponse(
        data=data,
        message="Trích xuất chỉ số tổng quan phân tích hoàn tất",
    )


@router.get(
    "/xu-huong",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER]))],
)
async def get_trends(
    days: int = Query(default=30, ge=1, le=365),
    from_date: Optional[str] = Query(default=None),
    to_date: Optional[str] = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    data = await AnalyticsService.get_author_timeseries(
        user_id=str(current_user.id),
        days=days,
        from_date=from_date,
        to_date=to_date,
    )
    return APIResponse(
        data=data,
        message="Trích xuất số liệu xu hướng phân tích hoàn tất",
    )


@router.get(
    "/tai-lieu",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER]))],
)
async def get_documents_analytics(
    search: Optional[str] = Query(default=None),
    sort_by: str = Query(default="revenue"),
    sort_order: str = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    from_date: Optional[str] = Query(default=None),
    to_date: Optional[str] = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    data = await AnalyticsService.get_author_documents_analytics(
        user_id=str(current_user.id),
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
        from_date=from_date,
        to_date=to_date,
    )
    return APIResponse(
        data=data,
        message="Trích xuất hiệu suất tài liệu phân tích hoàn tất",
    )


@router.get(
    "/he-thong",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_system_analytics(
    from_date: Optional[str] = Query(default=None),
    to_date: Optional[str] = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    data = await AnalyticsService.get_system_analytics(
        from_date=from_date,
        to_date=to_date,
    )
    return APIResponse(
        data=data,
        message="Trích xuất báo cáo phân tích toàn hệ thống hoàn tất",
    )


@router.get(
    "/ket-xuat",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER]))],
)
async def export_analytics(
    format: str = Query(default="json"),
    scope: str = Query(default="author"),
    from_date: Optional[str] = Query(default=None),
    to_date: Optional[str] = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    is_admin = current_user.role == Role.ADMIN
    data = await AnalyticsService.export_analytics(
        user_id=str(current_user.id),
        is_admin=is_admin,
        format_type=format,
        scope=scope,
        from_date=from_date,
        to_date=to_date,
    )
    return APIResponse(
        data=data,
        message="Kết xuất báo cáo phân tích dữ liệu hoàn tất",
    )
