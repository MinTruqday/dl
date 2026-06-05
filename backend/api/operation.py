from typing import Any, List, Optional
from fastapi import APIRouter, Depends, status
from models.user import UserInDB, RoleEnum
from api.dependency import require_role, get_current_user
from core.response import APIResponse
from services.operation import OperationService
from services.withdrawal import WithdrawalService
from services.user import UserService
from models.operation import CampaignRequest, ApplicationReviewRequest
router = APIRouter(prefix='/van-hanh')

@router.get('/chi-so', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_system_metrics(db=Depends(get_db)):
    return APIResponse(data=await OperationService.get_system_health(db=db), message='Lấy thông số hệ thống thành công')

@router.get('/bao-tri', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_maintenance_status(db=Depends(get_db)):
    return APIResponse(data=await OperationService.get_maintenance_mode(db=db), message='Lấy trạng thái bảo trì thành công')

@router.post('/bao-tri', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def toggle_maintenance(enabled: bool, db=Depends(get_db)):
    return APIResponse(data=await OperationService.toggle_maintenance_mode(enabled, db=db), message='Cập nhật trạng thái bảo trì thành công')

@router.get('/rut-tien', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_withdrawals_list(status: str='PENDING', db=Depends(get_db)):
    return APIResponse(data=await WithdrawalService.get_withdrawal_queue(status, db=db), message='Lấy danh sách thanh toán thành công')

@router.post('/sao-luu', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def trigger_backup(db=Depends(get_db)):
    return APIResponse(data=await OperationService.trigger_backup(db=db), message='Đã khởi tạo quá trình sao lưu hệ thống')

@router.post('/khoa-api', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def create_api_key(name: str, db=Depends(get_db)):
    return APIResponse(data=await OperationService.create_api_key(name, db=db), message='Tạo khóa API thành công')

@router.post('/tiep-thi/chien-dich', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def create_marketing_campaign(payload: CampaignRequest, db=Depends(get_db)):
    return APIResponse(data=await OperationService.create_marketing_campaign(payload.model_dump(), db=db), message='Khởi tạo chiến dịch tiếp thị thành công')

@router.get('/don-ung-tuyen/tac-gia', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_author_applications(status: str='PENDING', db=Depends(get_db)):
    return APIResponse(data=await OperationService.get_author_applications(status, db=db), message='Lấy danh sách đơn ứng tuyển thành công')

@router.put('/don-ung-tuyen/tac-gia/{application_id}/xet-duyet', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def review_author_application(application_id: str, payload: ApplicationReviewRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await OperationService.review_author_application(application_id, payload.status, payload.reason or '', str(current_user.id), db=db), message='Xử lý đơn ứng tuyển thành công')

@router.get('/cau-hinh', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_system_config(db=Depends(get_db)):
    return APIResponse(data={}, message='Lấy cấu hình hệ thống thành công')

@router.get('/suc-khoe-he-thong', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_system_health(db=Depends(get_db)):
    return APIResponse(data=await OperationService.get_system_health(db=db), message='Lấy trạng thái hệ thống thành công')

@router.get('/bao-cao', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_admin_reports(db=Depends(get_db)):
    return APIResponse(data=await UserService.get_report_queue(status_filter=None, db=db), message='Lấy danh sách báo cáo thành công')

@router.get('/thu-thap/thong-ke', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_collector_stats(db=Depends(get_db)):
    return APIResponse(data=await OperationService.get_collector_stats(db=db), message='Lấy thông số thu thập thành công')

@router.post('/nguoi-dung/{user_id}/shadowban', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def shadowban_user(user_id: str, is_banned: bool, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await UserService.shadowban_user(user_id, is_banned, current_user, db=db), message='Cập nhật shadowban thành công')

@router.post('/nguoi-dung/{user_id}/kyc/{status}', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def verify_kyc(user_id: str, status: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await UserService.verify_kyc(user_id, status, current_user, db=db), message='Xử lý KYC thành công')

@router.get('/minio/thong-ke', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_minio_stats(db=Depends(get_db)):
    return APIResponse(data=await OperationService.get_minio_stats(db=db), message='Lấy thông số lưu trữ MinIO thành công')