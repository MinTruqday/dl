from typing import Any, List
from fastapi import APIRouter, Depends, Query
from api.dependency import get_current_user
from models.user import UserInDB
from models.library import TypographyRequest, ProgressUpdate, ReadingGoalCreate, PinnedDocumentRequest
from core.response import APIResponse
from services.read import ReadService
from pydantic import BaseModel

router = APIRouter(prefix="/doc")




@router.get("/lich-su", response_model=APIResponse[Any])
async def get_history(cursor: str = None, limit: int = Query(20), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ReadService.get_reading_history(current_user, cursor, limit),
        message="Lấy lịch sử đọc thành công"
    )

@router.post("/tien-do", response_model=APIResponse[Any])
async def update_progress(data: ProgressUpdate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ReadService.update_progress(data, current_user),
        message="Cập nhật tiến độ thành công"
    )

@router.get("/dang-doc", response_model=APIResponse[Any])
async def get_continue_reading(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ReadService.get_continue_reading(current_user),
        message="Lấy danh sách đang đọc thành công"
    )

@router.post("/muc-tieu", response_model=APIResponse[Any])
async def set_reading_goal(data: ReadingGoalCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ReadService.set_reading_goal(data, current_user),
        message="Thiết lập mục tiêu thành công",
        status=201
    )

@router.get("/muc-tieu", response_model=APIResponse[Any])
async def get_reading_goal(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ReadService.get_reading_goal(current_user),
        message="Lấy thông tin mục tiêu thành công"
    )
@router.put("/trinh-bay", response_model=APIResponse[Any])
async def update_typography(data: TypographyRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ReadService.update_typography(data, current_user),
        message="Cập nhật hiển thị thành công"
    )

@router.get("/tai-lieu/{document_id}/tim-kiem", response_model=APIResponse[Any])
async def search_in_document(document_id: str, q: str = Query(...), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ReadService.search_in_document(document_id, q, current_user),
        message="Tìm kiếm trong tài liệu thành công"
    )

# Secondary router matching frontend history deletions
reader_router = APIRouter(prefix="/reader")

@reader_router.delete("/history", response_model=APIResponse[Any])
async def clear_reading_history(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ReadService.clear_reading_history(current_user),
        message="Xóa toàn bộ lịch sử đọc thành công"
    )

@reader_router.delete("/history/{document_id}", response_model=APIResponse[Any])
async def delete_history_item(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ReadService.delete_history_item(document_id, current_user),
        message="Xóa mục lịch sử đọc thành công"
    )
