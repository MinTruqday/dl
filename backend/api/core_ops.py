from fastapi import APIRouter, Depends, BackgroundTasks
from api.dependencies import get_current_user
from services.editor import EditorService
from services.profile import ProfileService
from models.user import UserInDB

router = APIRouter()

@router.post("/author/documents/{document_id}/global-replace")
async def global_find_replace(document_id: str, payload: dict, current_user: UserInDB = Depends(get_current_user)):
    search_term = payload.get("search")
    replace_term = payload.get("replace")
    match_case = payload.get("match_case", False)
    return await EditorService.global_find_replace(document_id, search_term, replace_term, match_case, current_user)

@router.post("/gdpr/takeout")
async def generate_gdpr_takeout(background_tasks: BackgroundTasks, current_user: UserInDB = Depends(get_current_user)):
    background_tasks.add_task(ProfileService.generate_gdpr_takeout, current_user)
    return {"status": "processing", "message": "Đang chuẩn bị dữ liệu. Vui lòng chờ."}

@router.delete("/gdpr/forget-me")
async def right_to_be_forgotten(current_user: UserInDB = Depends(get_current_user)):
    return await ProfileService.right_to_be_forgotten(current_user)
