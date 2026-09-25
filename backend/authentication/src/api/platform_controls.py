from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from src.schemas.platform import (
    ActionReason,
    BreakGlassCreateRequest,
    BulkUserConfirmRequest,
    BulkUserPreviewRequest,
    CacheClearRequest,
    ConfigUpdate,
    EmergencyRevokeRequest,
    MaintenanceModeRequest,
    ProjectDeleteRequest,
    RagReindexRequest,
    SecretReferenceRequest,
    SecretReferenceRotateRequest,
    ServiceIdentityRequest,
    ServiceIdentityRotateRequest,
    SmtpTestRequest,
    UserDeleteRequest,
)
from src.services.platform import (
    get_platform_config,
    require_system_admin,
    update_platform_config,
)
from src.core.dependency import CurrentUser, get_current_user
from src.core.response import APIResponse
from src.services.platform_account_controls import PlatformAccountControlService
from src.services.platform_control_operations import PlatformControlOperationsService
from src.services.platform_operations import PlatformOperationsService
from src.services.platform_projects import PlatformProjectService
from src.services.platform_security import PlatformSecurityService


router = APIRouter(
    prefix="/quan-tri", tags=["Quản trị nền tảng"], dependencies=[Depends(require_system_admin)]
)


@router.post("/tai-khoan/{user_id}/gui-lai-xac-minh", response_model=APIResponse[Any])
async def resend_account_activation(
    user_id: str,
    payload: ActionReason,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
):
    return APIResponse(
        data=await PlatformAccountControlService.resend_activation(
            user_id,
            payload,
            request.client.host if request.client else "admin",
            current_user,
        ),
        message="Gửi lại quy trình kích hoạt tài khoản hoàn tất",
    )


@router.delete("/tai-khoan/{user_id}", response_model=APIResponse[Any])
async def anonymize_user(
    user_id: str, payload: UserDeleteRequest, current_user: CurrentUser = Depends(get_current_user)
):
    return APIResponse(
        data=await PlatformAccountControlService.anonymize(user_id, payload, current_user),
        message="Ẩn danh và vô hiệu hóa tài khoản hoàn tất",
    )


@router.post("/tai-khoan/hang-loat/xem-truoc", response_model=APIResponse[Any], status_code=201)
async def preview_bulk_user_action(
    payload: BulkUserPreviewRequest, current_user: CurrentUser = Depends(get_current_user)
):
    return APIResponse(
        data=await PlatformAccountControlService.preview_bulk(payload, current_user),
        message="Tạo bản xem trước thao tác hàng loạt hoàn tất",
        status=201,
    )


@router.post("/tai-khoan/hang-loat/{operation_id}/xac-nhan", response_model=APIResponse[Any])
async def confirm_bulk_user_action(
    operation_id: str,
    payload: BulkUserConfirmRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    return APIResponse(
        data=await PlatformAccountControlService.confirm_bulk(operation_id, current_user),
        message="Hoàn tất thao tác tài khoản hàng loạt",
    )


@router.get("/du-an/{project_id}/vai-tro-du-an", response_model=APIResponse[Any])
async def project_membership_diagnostics(
    project_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    return APIResponse(
        data=await PlatformProjectService.membership_diagnostics(project_id, current_user),
        message="Tải chẩn đoán thành viên dự án hoàn tất",
    )


@router.delete("/du-an/{project_id}", response_model=APIResponse[Any])
async def hard_delete_project(
    project_id: str,
    payload: ProjectDeleteRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    return APIResponse(
        data=await PlatformProjectService.hard_delete(project_id, payload, current_user),
        message="Xóa dự án theo quy trình quản trị hoàn tất",
    )


@router.get("/bao-mat/truy-cap-khan-cap", response_model=APIResponse[Any])
async def list_break_glass_grants(
    active_only: bool = True, current_user: CurrentUser = Depends(get_current_user)
):
    return APIResponse(
        data=await PlatformProjectService.break_glass_grants(active_only),
        message="Tải quyền truy cập khẩn cấp hoàn tất",
    )


@router.post("/bao-mat/truy-cap-khan-cap", response_model=APIResponse[Any], status_code=201)
async def create_break_glass_grant(
    payload: BreakGlassCreateRequest, current_user: CurrentUser = Depends(get_current_user)
):
    return APIResponse(
        data=await PlatformProjectService.create_break_glass(payload, current_user),
        message="Cấp quyền truy cập khẩn cấp hoàn tất",
        status=201,
    )


@router.post("/bao-mat/truy-cap-khan-cap/{grant_id}/thu-hoi", response_model=APIResponse[Any])
async def revoke_break_glass_grant(
    grant_id: str, payload: ActionReason, current_user: CurrentUser = Depends(get_current_user)
):
    return APIResponse(
        data=await PlatformProjectService.revoke_break_glass(grant_id, payload, current_user),
        message="Thu hồi quyền truy cập khẩn cấp hoàn tất",
    )


@router.get("/bao-mat/gioi-han-tan-suat", response_model=APIResponse[Any])
async def get_rate_limits(current_user: CurrentUser = Depends(get_current_user)):
    return await get_platform_config("rate_limits", current_user)


@router.patch("/bao-mat/gioi-han-tan-suat", response_model=APIResponse[Any])
async def update_rate_limits(
    payload: ConfigUpdate, current_user: CurrentUser = Depends(get_current_user)
):
    return await update_platform_config("rate_limits", payload, current_user)


@router.get("/bao-mat/danh-tinh-dich-vu", response_model=APIResponse[Any])
async def list_service_identities(current_user: CurrentUser = Depends(get_current_user)):
    return APIResponse(
        data=await PlatformSecurityService.service_identities(),
        message="Tải danh tính dịch vụ hoàn tất",
    )


@router.post("/bao-mat/danh-tinh-dich-vu", response_model=APIResponse[Any], status_code=201)
async def create_service_identity(
    payload: ServiceIdentityRequest, current_user: CurrentUser = Depends(get_current_user)
):
    return APIResponse(
        data=await PlatformSecurityService.create_service_identity(payload, current_user),
        message="Tạo danh tính dịch vụ hoàn tất",
        status=201,
    )


@router.post("/bao-mat/danh-tinh-dich-vu/{identity_id}/xoay-vong", response_model=APIResponse[Any])
async def rotate_service_identity(
    identity_id: str,
    payload: ServiceIdentityRotateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    return APIResponse(
        data=await PlatformSecurityService.rotate_service_identity(
            identity_id, payload, current_user
        ),
        message="Luân chuyển tham chiếu danh tính dịch vụ hoàn tất",
    )


@router.post("/bao-mat/thu-hoi-khan-cap", response_model=APIResponse[Any])
async def emergency_revoke(
    payload: EmergencyRevokeRequest, current_user: CurrentUser = Depends(get_current_user)
):
    return APIResponse(
        data=await PlatformSecurityService.emergency_revoke(payload, current_user),
        message="Thu hồi khẩn cấp hoàn tất",
    )


@router.get("/bao-mat/nhat-ky", response_model=APIResponse[Any])
async def security_audit(
    action: str = Query(default="", max_length=100),
    actor: str = Query(default="", max_length=320),
    limit: int = Query(default=200, ge=1, le=2000),
    current_user: CurrentUser = Depends(get_current_user),
):
    return APIResponse(
        data=await PlatformSecurityService.audit(action, actor, limit),
        message="Tải nhật ký bảo mật hoàn tất",
    )


@router.get("/bi-mat", response_model=APIResponse[Any])
async def list_secret_references(current_user: CurrentUser = Depends(get_current_user)):
    return APIResponse(
        data=await PlatformSecurityService.secret_references(),
        message="Tải tham chiếu bí mật hoàn tất",
    )


@router.post("/bi-mat", response_model=APIResponse[Any], status_code=201)
async def create_secret_reference(
    payload: SecretReferenceRequest, current_user: CurrentUser = Depends(get_current_user)
):
    return APIResponse(
        data=await PlatformSecurityService.create_secret_reference(payload, current_user),
        message="Tạo tham chiếu bí mật hoàn tất",
        status=201,
    )


@router.post("/bi-mat/{reference_id}/xoay-vong", response_model=APIResponse[Any])
async def rotate_secret_reference(
    reference_id: str,
    payload: SecretReferenceRotateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    return APIResponse(
        data=await PlatformSecurityService.rotate_secret_reference(
            reference_id, payload, current_user
        ),
        message="Luân chuyển tham chiếu bí mật hoàn tất",
    )


@router.delete("/bi-mat/{reference_id}", response_model=APIResponse[Any])
async def delete_secret_reference(
    reference_id: str, payload: ActionReason, current_user: CurrentUser = Depends(get_current_user)
):
    return APIResponse(
        data=await PlatformSecurityService.delete_secret_reference(
            reference_id, payload, current_user
        ),
        message="Xóa tham chiếu bí mật hoàn tất",
    )


@router.post("/tich-hop/smtp/kiem-tra", response_model=APIResponse[Any])
async def test_smtp(
    payload: SmtpTestRequest, current_user: CurrentUser = Depends(get_current_user)
):
    return APIResponse(
        data=await PlatformOperationsService.test_smtp(payload, current_user),
        message="Gửi thư kiểm tra hoàn tất",
    )


@router.get("/van-hanh/hang-doi", response_model=APIResponse[Any])
async def queue_overview(current_user: CurrentUser = Depends(get_current_user)):
    return APIResponse(
        data=await PlatformOperationsService.queue_overview(),
        message="Tải trạng thái hàng đợi hoàn tất",
    )


@router.post(
    "/van-hanh/dlq/{job_id}/dua-lai-hang-doi", response_model=APIResponse[Any], status_code=202
)
async def requeue_dead_letter_job(
    job_id: str, payload: ActionReason, current_user: CurrentUser = Depends(get_current_user)
):
    return APIResponse(
        data=await PlatformOperationsService.requeue_dead_letter_job(
            job_id, payload, current_user
        ),
        message="Đưa tác vụ lỗi trở lại hàng đợi hoàn tất",
        status=202,
    )


@router.get("/van-hanh/rag", response_model=APIResponse[Any])
async def rag_operations(current_user: CurrentUser = Depends(get_current_user)):
    return APIResponse(
        data=await PlatformOperationsService.rag_operations(),
        message="Tải trạng thái lập chỉ mục tri thức hoàn tất",
    )


@router.post("/van-hanh/rag/lap-chi-muc-lai", response_model=APIResponse[Any], status_code=202)
async def request_rag_reindex(
    payload: RagReindexRequest, current_user: CurrentUser = Depends(get_current_user)
):
    return APIResponse(
        data=await PlatformControlOperationsService.request_rag_reindex(payload, current_user),
        message="Tiếp nhận yêu cầu lập chỉ mục lại hoàn tất",
        status=202,
    )


@router.get("/van-hanh/bo-nho-dem", response_model=APIResponse[Any])
async def inspect_safe_caches(current_user: CurrentUser = Depends(get_current_user)):
    return APIResponse(
        data=await PlatformControlOperationsService.inspect_caches(),
        message="Tải trạng thái bộ đệm an toàn hoàn tất",
    )


@router.post("/van-hanh/bo-nho-dem/don-sach", response_model=APIResponse[Any])
async def clear_safe_caches(
    payload: CacheClearRequest, current_user: CurrentUser = Depends(get_current_user)
):
    return APIResponse(
        data=await PlatformControlOperationsService.clear_caches(payload, current_user),
        message="Xóa bộ đệm an toàn hoàn tất",
    )


@router.get("/van-hanh/dung-luong-luu-tru", response_model=APIResponse[Any])
async def storage_usage(current_user: CurrentUser = Depends(get_current_user)):
    return APIResponse(
        data=await PlatformOperationsService.storage_usage(),
        message="Tải dung lượng lưu trữ hoàn tất",
    )


@router.get("/van-hanh/phien-ban-van-hanh", response_model=APIResponse[Any])
async def runtime_versions(current_user: CurrentUser = Depends(get_current_user)):
    return APIResponse(
        data=await PlatformControlOperationsService.runtime_versions(),
        message="Tải phiên bản vận hành hoàn tất",
    )


@router.get("/cau-hinh/bao-tri", response_model=APIResponse[Any])
async def get_maintenance_mode(current_user: CurrentUser = Depends(get_current_user)):
    return await get_platform_config("maintenance", current_user)


@router.patch("/cau-hinh/bao-tri", response_model=APIResponse[Any])
async def update_maintenance_mode(
    payload: MaintenanceModeRequest, current_user: CurrentUser = Depends(get_current_user)
):
    return await update_platform_config(
        "maintenance",
        ConfigUpdate(
            values={"enabled": payload.enabled, "banner": payload.banner}, reason=payload.reason
        ),
        current_user,
    )


def config_routes(config_type: str):
    async def get_value(current_user: CurrentUser = Depends(get_current_user)):
        return await get_platform_config(config_type, current_user)

    async def update_value(
        payload: ConfigUpdate, current_user: CurrentUser = Depends(get_current_user)
    ):
        return await update_platform_config(config_type, payload, current_user)

    return get_value, update_value


for route_path, config_type in [
    ("/cau-hinh/co-tinh-nang", "feature_flags"),
    ("/cau-hinh/dia-phuong-hoa", "localization"),
    ("/cau-hinh/luu-giu", "retention"),
    ("/cau-hinh/han-muc-mac-dinh", "default_quotas"),
    ("/cau-hinh/nhap-xuat", "import_export"),
    ("/bao-mat/chinh-sach-truy-cap-khan-cap", "break_glass_policy"),
    ("/ai/gioi-han", "ai_limits"),
    ("/ai/truy-xuat", "ai_retrieval"),
]:
    get_handler, update_handler = config_routes(config_type)
    router.add_api_route(
        route_path,
        get_handler,
        methods=["GET"],
        response_model=APIResponse[Any],
        name=f"get_{config_type}",
    )
    router.add_api_route(
        route_path,
        update_handler,
        methods=["PATCH"],
        response_model=APIResponse[Any],
        name=f"update_{config_type}",
    )
