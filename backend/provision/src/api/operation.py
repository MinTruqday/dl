from typing import Any, List, Optional
from fastapi import APIRouter, Depends, status
from core.schemas.user import UserInDB, RoleEnum
from src.api.dependency import get_db, require_role, get_current_user
from core.response import APIResponse
from src.services.operation import OperationService
from src.services.user import UserService
from src.schemas.operation import CampaignRequest, CollectionRequest
router = APIRouter(prefix='/van-hanh')

@router.get('/chi-so', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_system_metrics(db=Depends(get_db)):
    return APIResponse(data=await OperationService.get_system_telemetry(db=db), message='Đã tải dữ liệu hoạt động hệ thống')

@router.get('/bao-tri', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_maintenance_status(db=Depends(get_db)):
    return APIResponse(data=await OperationService.get_maintenance_mode(db=db), message='Đã cập nhật trạng thái bảo trì')

@router.post('/bao-tri', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def toggle_maintenance(enabled: bool, db=Depends(get_db)):
    return APIResponse(data=await OperationService.toggle_maintenance_mode(enabled, db=db), message='Đã cập nhật chế độ bảo trì')

@router.post('/sao-luu', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def trigger_backup(db=Depends(get_db)):
    return APIResponse(data=await OperationService.trigger_backup(db=db), message='Đã kích hoạt sao lưu hệ thống')

@router.post('/khoa-api', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def create_api_key(name: str, db=Depends(get_db)):
    return APIResponse(data=await OperationService.create_api_key(name, db=db), message='Đã tạo khóa truy cập mới')

@router.post('/tiep-thi/chien-dich', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def create_marketing_campaign(payload: CampaignRequest, db=Depends(get_db)):
    return APIResponse(data=await OperationService.create_marketing_campaign(payload.model_dump(), db=db), message='Đã tạo chiến dịch tiếp thị mới', status=201)


@router.get('/cau-hinh', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_system_config(db=Depends(get_db)):
    return APIResponse(data={}, message='Đã tải cấu hình hệ thống')

@router.get('/suc-khoe-he-thong', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_system_health(db=Depends(get_db)):
    return APIResponse(data=await OperationService.get_system_health(db=db), message='Đã tải báo cáo tình trạng hệ thống')

@router.get('/bao-cao', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_admin_reports(db=Depends(get_db)):
    return APIResponse(data=await UserService.get_report_queue(status_filter=None, db=db), message='Đã tải danh sách báo cáo vi phạm')

@router.get('/thu-thap/thong-ke', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_collector_stats(db=Depends(get_db)):
    return APIResponse(data=await OperationService.get_collector_stats(db=db), message='Đã tổng hợp dữ liệu thống kê')

@router.post('/thu-thap/kich-hoat', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def trigger_collection(req: CollectionRequest, db=Depends(get_db)):
    return APIResponse(data=await OperationService.trigger_collection(req.source, req.pages, db=db), message='Đã kích hoạt trình thu thập')

@router.post('/thu-thap/dung', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def stop_collection(db=Depends(get_db)):
    return APIResponse(data=await OperationService.stop_collection(db=db), message='Đã gửi lệnh dừng trình thu thập')

@router.get('/thu-thap/logs', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_collector_logs(db=Depends(get_db)):
    return APIResponse(data=await OperationService.get_collector_logs(db=db), message='Đã tải logs từ trình thu thập')

@router.get('/thu-thap/cong-viec-dang-chay', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_active_collector_jobs(db=Depends(get_db)):
    return APIResponse(data=await OperationService.get_active_collector_jobs(db=db), message='Đã tải danh sách công việc đang chạy')

@router.post('/nguoi-dung/{user_id}/shadowban', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def shadowban_user(payload: Any, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await OperationService.bulk_update_shadowban(payload.user_ids, payload.status, current_user, db=db), message='Đã áp dụng trạng thái hạn chế')

@router.post('/nguoi-dung/{user_id}/kyc/{status}', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def verify_kyc(payload: Any, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await OperationService.bulk_verify_kyc(payload.user_ids, payload.status, current_user, db=db), message='Đã xử lý hồ sơ định danh')

@router.get('/minio/thong-ke', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_minio_stats(db=Depends(get_db)):
    return APIResponse(data=await OperationService.get_minio_stats(db=db), message='Đã tải thống kê lưu trữ')