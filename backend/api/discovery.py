from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query, status
from models.user import UserInDB
from api.dependency import get_db, get_current_user_optional
from core.response import APIResponse
from services.document import DocumentService

router = APIRouter(prefix='/kham-pha')

@router.get('/xu-huong', response_model=APIResponse[Any])
async def get_trending_documents(limit: int=5, db=Depends(get_db)):
    return APIResponse(data=await DocumentService.get_trending_documents(limit), message='Lấy danh sách tài liệu xu hướng thành công', status=status.HTTP_200_OK)

@router.get('/phan-loai', response_model=APIResponse[Any])
async def get_tags_categories(db=Depends(get_db)):
    return APIResponse(data=await DocumentService.get_tags_categories(), message='Lấy danh sách thẻ và danh mục thành công', status=status.HTTP_200_OK)

@router.get('/tim-kiem-thong-minh', response_model=APIResponse[Any])
async def smart_search(query: str, limit: int=10, current_user: UserInDB=Depends(get_current_user_optional), db=Depends(get_db)):
    if not current_user:
        return APIResponse(data=await DocumentService.get_text_search(query, limit), message='Tìm kiếm văn bản cơ bản')
    
    import httpx
    from core.config import settings
    from fastapi import HTTPException
    from loguru import logger
    
    rag_url = getattr(settings, 'AGENTIC_AI_URL', None)
    if not rag_url:
        return APIResponse(data=await DocumentService.get_text_search(query, limit), message='Hệ thống AI chưa được cấu hình, dùng tìm kiếm cơ bản')
        
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f'{rag_url}/tro-chuyen', 
                json={'query': f'Tìm kiếm tài liệu liên quan đến: {query}', 'user_id': str(current_user.id), 'useSmart': True}
            )
            if resp.status_code == 200:
                result = resp.json()
                return APIResponse(data=result, message='Tìm kiếm thông minh AI thành công')
            else:
                logger.error(f"AI: Smart search failed for '{query}': {resp.status_code}")
                return APIResponse(data=await DocumentService.get_text_search(query, limit), message='Lỗi kết nối AI, dùng tìm kiếm cơ bản')
    except Exception as e:
        logger.error(f"AI: Smart search exception for '{query}': {e}")
        return APIResponse(data=await DocumentService.get_text_search(query, limit), message='Lỗi kết nối AI, dùng tìm kiếm cơ bản')

@router.get('/goi-y/ai', response_model=APIResponse[Any])
async def get_ai_recommendations(limit: int=10, current_user: UserInDB=Depends(get_current_user_optional), db=Depends(get_db)):
    return APIResponse(data=await DocumentService.get_trending_documents(limit), message='Lấy gợi ý tài liệu từ AI thành công')

@router.get('/hashtag-xu-huong', response_model=APIResponse[Any])
async def get_trending_tags(limit: int=10, db=Depends(get_db)):
    return APIResponse(data=await DocumentService.get_trending_tags(limit), message='Lấy danh sách hashtag xu hướng thành công', status=status.HTTP_200_OK)