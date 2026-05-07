from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query, status
from models.user import UserInDB
from api.dependency import get_current_user_optional
from core.response import APIResponse
from services.document import DocumentService
from services.feed import SocialFeedService
from services.ranking import RankingService
from services.auth import AuthService

router = APIRouter(prefix="/discovery")

@router.get("/trending", response_model=APIResponse[Any])
async def get_trending_documents(limit: int = 5):
    return APIResponse(
        data=await DocumentService.get_trending_documents(limit), 
        message="Lấy danh sách tài liệu xu hướng thành công.", 
        status=status.HTTP_200_OK
    )

@router.get("/tags-and-categories", response_model=APIResponse[Any])
async def get_tags_categories():
    return APIResponse(
        data=await DocumentService.get_tags_categories(), 
        message="Lấy danh sách thẻ và danh mục thành công.", 
        status=status.HTTP_200_OK
    )

@router.get("/semantic-search", response_model=APIResponse[Any])
async def semantic_search(query: str, limit: int = 10):
    return APIResponse(
        data=await DocumentService.get_semantic_search(query, limit), 
        message="Tìm kiếm ngữ nghĩa thành công.", 
        status=status.HTTP_200_OK
    )

@router.get("/recommendations/ai", response_model=APIResponse[Any])
async def get_ai_recommendations(limit: int = 10, current_user: UserInDB = Depends(get_current_user_optional)):
    return APIResponse(
        data=await DocumentService.get_ai_recommendations(limit), 
        message="Lấy gợi ý tài liệu từ AI thành công.", 
        status=200
    )

@router.get("/featured-authors", response_model=APIResponse[Any])
async def get_featured_authors(limit: int = 10):
    return APIResponse(
        data=await RankingService.get_featured_authors(limit),
        message="Lấy danh sách tác giả nổi bật thành công."
    )

@router.get("/trending-tags", response_model=APIResponse[Any])
async def get_trending_tags(limit: int = 10):
    return APIResponse(
        data=await SocialFeedService.get_trending_tags(limit), 
        message="Lấy danh sách hashtag xu hướng thành công.", 
        status=status.HTTP_200_OK
    )
