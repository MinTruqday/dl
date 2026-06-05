from typing import Any, Optional
from fastapi import APIRouter, Depends
from api.dependency import get_db, get_current_user
from models.user import UserInDB
from models.review import RatingRequest, ChapterRatingRequest
from models.feedback import ReportRequest, TypoReportRequest
from core.response import APIResponse
from services.review import ReviewService
from pydantic import BaseModel
router = APIRouter(prefix='/phan-hoi')

@router.post('/bao-cao', response_model=APIResponse[Any])
async def report_content(req: ReportRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await ReviewService.report_content(req, current_user, db=db), message='Báo cáo nội dung vi phạm thành công')

@router.post('/tai-lieu/{document_id}/danh-gia', response_model=APIResponse[Any])
async def rate_document(document_id: str, data: RatingRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await ReviewService.rate_document(document_id, data, current_user, db=db), message='Đánh giá tài liệu thành công')

@router.post('/tai-lieu/{document_id}/chuong/danh-gia', response_model=APIResponse[Any])
async def rate_chapter(document_id: str, data: ChapterRatingRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await ReviewService.rate_chapter(document_id, data, current_user, db=db), message='Đánh giá chương thành công')

@router.post('/tai-lieu/{document_id}/loi-chinh-ta', response_model=APIResponse[Any])
async def report_typo(document_id: str, data: TypoReportRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await ReviewService.report_typo(document_id, data, current_user, db=db), message='Gửi báo cáo lỗi chính tả thành công', status=201)

@router.get('/tai-lieu/{document_id}/loi-chinh-ta', response_model=APIResponse[Any])
async def get_typo_reports(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await ReviewService.get_typo_reports(document_id, current_user, db=db), message='Lấy danh sách báo cáo thành công')