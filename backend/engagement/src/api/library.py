from typing import Any

from fastapi import APIRouter, Depends

from src.api.dependency import CurrentUser, get_current_user
from src.core.response import APIResponse
from src.schemas.library import ReadingListCreate
from src.services.library import LibraryService


router = APIRouter(prefix="/thu-vien")


@router.post("/danh-sach", response_model=APIResponse[Any], status_code=201)
async def create_reading_list(
    data: ReadingListCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    return APIResponse(
        data=await LibraryService.create_reading_list(data, current_user),
        message="Khởi tạo danh sách đọc tài liệu mới hoàn tất",
        status=201,
    )


@router.get("/danh-sach", response_model=APIResponse[Any])
async def get_my_lists(
    current_user: CurrentUser = Depends(get_current_user),
):
    return APIResponse(
        data=await LibraryService.get_my_reading_lists(current_user),
        message="Trích xuất bộ sưu tập danh sách đọc hoàn tất",
    )


@router.get("/danh-sach/{list_id}", response_model=APIResponse[Any])
async def get_list_by_id(
    list_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    return APIResponse(
        data=await LibraryService.get_reading_list_by_id(list_id, current_user),
        message="Trích xuất nội dung chi tiết danh sách đọc hoàn tất",
    )


@router.post("/lists/{list_id}/documents/{document_id}", response_model=APIResponse[Any])
async def add_to_list(
    list_id: str,
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    return APIResponse(
        data=await LibraryService.add_document_to_list(
            list_id,
            document_id,
            current_user,
        ),
        message="Bổ sung tài liệu vào danh sách đọc hoàn tất",
    )


@router.delete("/lists/{list_id}/documents/{document_id}", response_model=APIResponse[Any])
async def remove_from_list(
    list_id: str,
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    return APIResponse(
        data=await LibraryService.remove_document_from_list(
            list_id,
            document_id,
            current_user,
        ),
        message="Loại bỏ tài liệu khỏi danh sách đọc hoàn tất",
    )
