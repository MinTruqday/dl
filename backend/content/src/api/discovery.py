from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query, status
from src.schemas.user import UserInDB
from src.api.dependency import get_db, get_current_user_optional
from src.core.response import APIResponse
from src.services.document import DocumentService
from src.services.ai import AIService
router = APIRouter(prefix='/kham-pha')

@router.get('/xu-huong', response_model=APIResponse[Any])
async def get_trending_documents(limit: int=5, db=Depends(get_db)):
    return APIResponse(data=await DocumentService.get_trending_documents(limit), message='Lấy danh sách tài liệu xu hướng thành công', status=status.HTTP_200_OK)

@router.get('/the-va-danh-muc', response_model=APIResponse[Any])
async def get_tags_categories(db=Depends(get_db)):
    return APIResponse(data=await DocumentService.get_tags_categories(), message='Lấy danh sách thẻ và danh mục thành công', status=status.HTTP_200_OK)

@router.get('/tim-kiem-thong-minh', response_model=APIResponse[Any])
async def smart_search(query: str, limit: int=10, current_user: UserInDB=Depends(get_current_user_optional), db=Depends(get_db)):
    if not current_user:
        return APIResponse(data=await DocumentService.get_text_search(query, limit), message='Tìm kiếm văn bản cơ bản (Vui lòng đăng nhập để dùng AI)')
    return APIResponse(data=await AIService.smart_search(query, current_user, db=db), message='Tìm kiếm thông minh AI thành công')

@router.get('/goi-y/ai', response_model=APIResponse[Any])
async def get_ai_recommendations(limit: int=10, current_user: UserInDB=Depends(get_current_user_optional), db=Depends(get_db)):
    return APIResponse(data=await AIService.get_ai_recommendations(limit, current_user, db=db), message='Lấy gợi ý tài liệu từ AI thành công')

@router.get('/hashtag-xu-huong', response_model=APIResponse[Any])
async def get_trending_tags(limit: int=10, db=Depends(get_db)):
    return APIResponse(data=await DocumentService.get_trending_tags(limit), message='Lấy danh sách hashtag xu hướng thành công', status=status.HTTP_200_OK)