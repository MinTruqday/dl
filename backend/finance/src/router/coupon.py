from typing import Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException
from src.api.dependency import get_db, require_role, get_current_user
from src.schemas.user import UserInDB, RoleEnum
from src.core.response import APIResponse
from src.services.coupon import CouponService
from src.schemas.wallet import CouponCreateRequest
router = APIRouter(prefix='/ma-uu-dai')

@router.get('/kiem-tra', response_model=APIResponse[Any])
async def validate_coupon(code: str, document_id: Optional[str]=None, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await CouponService.validate_coupon(code, current_user, document_id, db=db), message='Kiểm tra mã ưu đãi thành công')

@router.get('', response_model=APIResponse[Any])
async def get_coupons(current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    return APIResponse(data=await CouponService.get_coupons(current_user, db=db), message='Lấy danh sách mã ưu đãi thành công')

@router.post('', response_model=APIResponse[Any])
async def create_coupon(data: CouponCreateRequest, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    return APIResponse(data=await CouponService.create_coupon(data.model_dump(), current_user, db=db), message='Tạo mã ưu đãi thành công', status=201)

@router.post('/{coupon_id}/phe-duyet', response_model=APIResponse[Any])
async def approve_coupon(coupon_id: str, action: str='approve', current_user: UserInDB=Depends(require_role([RoleEnum.ADMIN])), db=Depends(get_db)):
    return APIResponse(data=await CouponService.approve_coupon(coupon_id, action, current_user, db=db), message='Xử lý phê duyệt thành công')

@router.patch('/{coupon_id}/trang-thai', response_model=APIResponse[Any])
async def toggle_coupon_status(coupon_id: str, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    return APIResponse(data=await CouponService.toggle_coupon_status(coupon_id, current_user, db=db), message='Cập nhật trạng thái thành công')

@router.delete('/{coupon_id}', response_model=APIResponse[Any])
async def delete_coupon(coupon_id: str, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    return APIResponse(data=await CouponService.delete_coupon(coupon_id, current_user, db=db), message='Xóa mã ưu đãi thành công')