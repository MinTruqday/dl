from typing import Any, List, Optional
from fastapi import APIRouter, Depends, status
from src.schemas.user import UserInDB, RoleEnum
from src.api.dependency import get_db, require_role, get_current_user
from core.response import APIResponse
from src.services.operation import OperationService
from src.services.withdrawal import WithdrawalService
from src.services.user import UserService
from src.schemas.operation import CampaignRequest, ApplicationReviewRequest
router = APIRouter(prefix='/van-hanh')

@router.get('/chi-so', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_system_metrics(db=Depends(get_db)):
    return APIResponse(data=await OperationService.get_system_health(db=db), message='Dữ liệu thông số hệ thống đã được tải success')

@router.get('/bao-tri', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_maintenance_status(db=Depends(get_db)):
    return APIResponse(data=await OperationService.get_maintenance_mode(db=db), message='Trạng thái bảo trì của hệ thống đã được cập nhật')

@router.post('/bao-tri', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def toggle_maintenance(enabled: bool, db=Depends(get_db)):
    return APIResponse(data=await OperationService.toggle_maintenance_mode(enabled, db=db), message='Hệ thống đã thay đổi chế độ bảo trì')

@router.post('/sao-luu', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def trigger_backup(db=Depends(get_db)):
    return APIResponse(data=await OperationService.trigger_backup(db=db), message='Tiến trình sao lưu dữ liệu hệ thống đã được kích hoạt')

@router.post('/khoa-api', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def create_api_key(name: str, db=Depends(get_db)):
    return APIResponse(data=await OperationService.create_api_key(name, db=db), message='API Key mới đã được tạo success')

@router.post('/tiep-thi/chien-dich', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def create_marketing_campaign(payload: CampaignRequest, db=Depends(get_db)):
    return APIResponse(data=await OperationService.create_marketing_campaign(payload.model_dump(), db=db), message='Chiến dịch tiếp thị mới đã được thiết lập')

@router.get('/don-ung-tuyen/tac-gia', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_author_applications(status: str='PENDING', db=Depends(get_db)):
    return APIResponse(data=await OperationService.get_author_applications(status, db=db), message='Danh sách đơn ứng tuyển của tác giả đã được tải về')

@router.put('/don-ung-tuyen/tac-gia/{application_id}/xet-duyet', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def review_author_application(application_id: str, payload: ApplicationReviewRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await OperationService.review_author_application(application_id, payload.status, payload.reason or '', str(current_user.id), db=db), message='Đơn ứng tuyển của tác giả đã được phê duyệt')

@router.get('/cau-hinh', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_system_config(db=Depends(get_db)):
    return APIResponse(data={}, message='Cấu hình hệ thống hiện tại đã được tải')

@router.get('/suc-khoe-he-thong', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_system_health(db=Depends(get_db)):
    return APIResponse(data=await OperationService.get_system_health(db=db), message='Báo cáo tình trạng sức khỏe hệ thống đã sẵn sàng')

@router.get('/bao-cao', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_admin_reports(db=Depends(get_db)):
    return APIResponse(data=await UserService.get_report_queue(status_filter=None, db=db), message='Danh sách báo cáo vi phạm đã được tải')

@router.get('/thu-thap/thong-ke', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_collector_stats(db=Depends(get_db)):
    return APIResponse(data=await OperationService.get_collector_stats(db=db), message='Dữ liệu thống kê thu thập đã được tổng hợp')

@router.post('/nguoi-dung/{user_id}/shadowban', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def shadowban_user(user_id: str, is_banned: bool, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await UserService.shadowban_user(user_id, is_banned, current_user, db=db), message='Thiết lập trạng thái hạn chế (shadowban) đã được áp dụng')

@router.post('/nguoi-dung/{user_id}/kyc/{status}', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def verify_kyc(user_id: str, status: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await UserService.verify_kyc(user_id, status, current_user, db=db), message='Hồ sơ định danh (KYC) của người dùng đã được xử lý')

@router.get('/minio/thong-ke', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_minio_stats(db=Depends(get_db)):
    return APIResponse(data=await OperationService.get_minio_stats(db=db), message='Dữ liệu thống kê không gian lưu trữ đã được tải')