from core.config import settings
from typing import Any, List, Optional

from core.response import APIResponse
from core.schemas.user import UserInDB
from fastapi import APIRouter, Depends, Query, status
from src.router.dependency_router import get_current_user_optional, get_db
from src.services.document_service import DocumentService

router = APIRouter(prefix="/discovery")


@router.get("/trending", response_model=APIResponse[Any])
async def get_trending_documents(
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentService.get_trending_documents(limit),
        message="Trending documents retrieved successfully",
        status=status.HTTP_200_OK,
    )


@router.get("/genres", response_model=APIResponse[Any])
async def get_tags_categories(db=Depends(get_db)):
    return APIResponse(
        data=await DocumentService.get_tags_categories(),
        message="Tags and categories retrieved successfully",
        status=status.HTTP_200_OK,
    )


@router.get("/smart-search", response_model=APIResponse[Any])
async def smart_search(
    query: str,
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    current_user: UserInDB = Depends(get_current_user_optional),
    db=Depends(get_db),
):
    if not current_user:
        return APIResponse(
            data=await DocumentService.get_text_search(query, limit),
            message="Basic text search",
        )

    import httpx
    from core.config import settings
    from fastapi import HTTPException
    from loguru import logger

    rag_url = settings.AGENTIC_AI_URL
    if not rag_url:
        return APIResponse(
            data=await DocumentService.get_text_search(query, limit),
            message="AI system is not configured, falling back to basic search",
        )

    try:
        async with httpx.AsyncClient(timeout=settings.LONG_PROCESS_TIMEOUT) as client:
            resp = await client.post(
                f"{rag_url}/chat",
                json={
                    "query": f"Searching for documents related to: {query}",
                    "user_id": str(current_user.id),
                    "useSmart": True,
                },
            )
            if resp.status_code == 200:
                result = resp.json()
                return APIResponse(
                    data=result, message="Smart AI search completed successfully"
                )
            else:
                logger.error(
                    "Smart search failed for query '{query}': {resp.status_code}"
                )
                return APIResponse(
                    data=await DocumentService.get_text_search(query, limit),
                    message="Switched to standard search successfully",
                )
    except Exception as e:
        logger.error("Smart search encountered an exception with query '{query}'")
        return APIResponse(
            data=await DocumentService.get_text_search(query, limit),
            message="Switched to standard search successfully",
        )


@router.get("/ai-suggestions", response_model=APIResponse[Any])
async def get_ai_recommendations(
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    current_user: UserInDB = Depends(get_current_user_optional),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentService.get_trending_documents(limit),
        message="AI document suggestions retrieved successfully",
    )


@router.get("/trending-hashtags", response_model=APIResponse[Any])
async def get_trending_tags(
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentService.get_trending_tags(limit),
        message="Trending hashtags retrieved successfully",
        status=status.HTTP_200_OK,
    )
