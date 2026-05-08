from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query, status
from models.user import UserInDB
from api.dependency import get_current_user_optional
from core.response import APIResponse
from services.document import DocumentService
from services.feed import FeedService
from services.rank import RankService
from services.ai import AIService

router = APIRouter(prefix="/kham-pha")

@router.get("/xu-huong", response_model=APIResponse[Any])
async def get_trending_documents(limit: int = 5):
    return APIResponse(
        data=await DocumentService.get_trending_documents(limit), 
        message="Lấy danh sách tài liệu xu hướng thành công", 
        status=status.HTTP_200_OK
    )

@router.get("/the-va-danh-muc", response_model=APIResponse[Any])
async def get_tags_categories():
    return APIResponse(
        data=await DocumentService.get_tags_categories(), 
        message="Lấy danh sách thẻ và danh mục thành công", 
        status=status.HTTP_200_OK
    )

@router.get("/tim-kiem-ngu-nghia", response_model=APIResponse[Any])
async def semantic_search(query: str, limit: int = 10, current_user: UserInDB = Depends(get_current_user_optional)):
    if not current_user:
        return APIResponse(data=await DocumentService.get_text_search(query, limit), message="Tìm kiếm văn bản cơ bản (Vui lòng đăng nhập để dùng AI)")
    return APIResponse(
        data=await AIService.semantic_search(query, current_user), 
        message="Tìm kiếm ngữ nghĩa AI thành công"
    )

@router.get("/goi-y/ai", response_model=APIResponse[Any])
async def get_ai_recommendations(limit: int = 10, current_user: UserInDB = Depends(get_current_user_optional)):
    return APIResponse(
        data=await AIService.get_ai_recommendations(limit), 
        message="Lấy gợi ý tài liệu từ AI thành công"
    )

@router.get("/tac-gia-noi-bat", response_model=APIResponse[Any])
async def get_featured_authors(limit: int = 10):
    return APIResponse(
        data=await RankService.get_featured_authors(limit),
        message="Lấy danh sách tác giả nổi bật thành công"
    )

@router.get("/hashtag-xu-huong", response_model=APIResponse[Any])
async def get_trending_tags(limit: int = 10):
    return APIResponse(
        data=await FeedService.get_trending_tags(limit), 
        message="Lấy danh sách hashtag xu hướng thành công", 
        status=status.HTTP_200_OK
    )
