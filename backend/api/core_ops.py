from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, BackgroundTasks
from api.dependencies import get_current_user
from services.editor import EditorService
from services.profile import ProfileService
from models.user import UserInDB

router = APIRouter()

@router.post("/author/documents/{document_id}/global-replace", response_model=APIResponse[Any])
async def global_find_replace(document_id: str, payload: dict, current_user: UserInDB = Depends(get_current_user)):
    search_term = payload.get("search")
    replace_term = payload.get("replace")
    match_case = payload.get("match_case", False)
    return APIResponse(data=await EditorService.global_find_replace(document_id, search_term, replace_term, match_case, current_user), message="Tìm kiếm và thay thế toàn cục thành công.", status=200)

@router.post("/gdpr/takeout", response_model=APIResponse[Any])
async def generate_gdpr_takeout(background_tasks: BackgroundTasks, current_user: UserInDB = Depends(get_current_user)):
    background_tasks.add_task(ProfileService.generate_gdpr_takeout, current_user)
    return APIResponse(data={"status": "processing"}, message="Yêu cầu trích xuất dữ liệu GDPR đang được xử lý. Bạn sẽ nhận được thông báo khi hoàn tất.", status=202)

@router.delete("/gdpr/forget-me", response_model=APIResponse[Any])
async def right_to_be_forgotten(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ProfileService.right_to_be_forgotten(current_user), message="Yêu cầu xóa dữ liệu vĩnh viễn đã được tiếp nhận.", status=200)
