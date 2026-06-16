from typing import Any
from core.dependency import get_current_user, get_db, require_role
from core.response import APIResponse
from fastapi import APIRouter, Depends
from src.schemas.management import CollectionRequest
from src.services.operations import OperationService
from src.services.users import UserService

router = APIRouter(prefix="/van-hanh")

@router.get("/chi-so", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_system_metrics(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_system_telemetry(db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.get("/bao-tri", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_maintenance_status(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_maintenance_mode(db=db),
        message="Khởi tạo AI thành công",
    )

@router.post("/bao-tri", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def toggle_maintenance(enabled: bool, db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.toggle_maintenance_mode(enabled, db=db),
        message="Khởi tạo AI thành công",
    )

@router.post("/sao-luu", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def trigger_backup(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.trigger_backup(db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )


@router.get("/cai-dat", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_system_config(db=Depends(get_db)):
    return APIResponse(
        data={},
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
    )

@router.get("/suc-khoe", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_system_health(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_system_health(db=db),
        message="Kiểm tra sức khỏe hệ thống hoàn tất và ổn định",
    )

@router.get("/bao-cao", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_admin_reports(db=Depends(get_db)):
    return APIResponse(
        data=await UserService.get_report_queue(status_filter=None, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.get("/thu-thap/thong-ke", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_collector_stats(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_collector_stats(db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.post("/thu-thap/kich-hoat", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def trigger_collection(req: CollectionRequest, db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.trigger_collection(req.source, req.pages, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.post("/thu-thap/dung-lai", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def stop_collection(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.stop_collection(db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.get("/thu-thap/nhat-ky", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_collector_logs(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_collector_logs(db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.get("/thu-thap/hoat-dong-cong-viec", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_active_collector_jobs(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_active_collector_jobs(db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.post("/nguoi-dung/{user_id}/cam-quyen-ngam", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def shadowban_user(payload: Any, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.bulk_update_shadowban(payload.user_ids, payload.status, current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.post("/nguoi-dung/{user_id}/kyc/{trang-thai}", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def verify_kyc(payload: Any, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.bulk_verify_kyc(payload.user_ids, payload.status, current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.get("/luu-tru/thong-ke", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_minio_stats(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_minio_stats(db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )