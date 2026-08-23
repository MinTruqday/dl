from typing import Any, List
from fastapi import APIRouter, Depends, Query
from src.core.response import APIResponse
from src.services.document import DocumentService
from src.api.dependency import get_current_user
from src.schemas.document import DocumentUpdate, TagsUpdate

router = APIRouter()


@router.get("/the-loai-va-nhan", response_model=APIResponse[Any])
async def get_tags_categories():
    return APIResponse(
        data=await DocumentService.get_tags_categories(),
        message="Truy xuất danh sách thể loại và nhãn thành công",
    )


@router.get("/nhan-thinh-hanh", response_model=APIResponse[List[str]])
async def get_trending_tags(limit: int = Query(default=20, le=100)):
    return APIResponse(
        data=await DocumentService.get_trending_tags(limit=limit),
        message="Truy xuất danh sách thẻ thịnh hành hoàn tất",
    )


@router.post("/{document_id}/danh-dau", response_model=APIResponse[Any])
async def toggle_star_document(document_id: str, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.toggle_star_document(document_id, current_user),
        message="Cập nhật trạng thái đánh dấu ưu tiên của tài liệu hoàn tất",
    )


@router.put("/{document_id}/the", response_model=APIResponse[Any])
async def update_tags(document_id: str, req: TagsUpdate, current_user=Depends(get_current_user)):
    result = await DocumentService.update_document(
        document_id, DocumentUpdate(tags=req.tags), current_user
    )
    return APIResponse(data=result, message="Cập nhật danh sách thẻ phân loại tài liệu hoàn tất")
