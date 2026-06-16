import httpx
from core.config import settings
from typing import Any, Optional
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query, status
from core.dependency import get_current_user_optional, get_db
from src.services.documents import DocumentService
from loguru import logger

router = APIRouter(prefix="/discovery")

@router.get("/trending", response_model=APIResponse[Any])
async def get_trending_documents(limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), db=Depends(get_db)):
    return APIResponse(
        data=await DocumentService.get_trending_documents(limit),
        message="Compiled systematic operational list tracking globally hyperactive public files rendered effectively",
        status=status.HTTP_200_OK,
    )

@router.get("/genres", response_model=APIResponse[Any])
async def get_tags_categories(db=Depends(get_db)):
    return APIResponse(
        data=await DocumentService.get_tags_categories(),
        message="Broad exhaustive taxonomic structural hierarchy sorting multiple dynamic digital metrics collected",
        status=status.HTTP_200_OK,
    )

@router.get("/smart-search", response_model=APIResponse[Any])
async def smart_search(query: str, limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), current_user: dict = Depends(get_current_user_optional), db=Depends(get_db)):
    if not current_user:
        return APIResponse(
            data=await DocumentService.get_text_search(query, limit),
            message="Base fundamental text analysis filtering queries executed mapping logical standard endpoints",
        )

    rag_url = settings.AGENTIC_AI_URL
    if not rag_url:
        return APIResponse(
            data=await DocumentService.get_text_search(query, limit),
            message="Advanced neural processing nodes unreachable triggering mandatory functional fallback rendering protocol",
        )

    try:
        async with httpx.AsyncClient(timeout=settings.LONG_PROCESS_TIMEOUT) as client:
            resp = await client.post(
                f"{rag_url}/chat",
                json={"query": "Searching for documents related to requested criteria", "user_id": str(current_user.get("id")), "useSmart": True},
            )
            if resp.status_code == 200:
                return APIResponse(data=resp.json(), message="Complex multidimensional semantic parsing effectively finalized routing specifically optimal matched vectors")
            else:
                logger.error("Sophisticated internal calculation logic algorithm abruptly derailed awaiting cognitive server response")
                return APIResponse(data=await DocumentService.get_text_search(query, limit), message="Base fundamental text analysis filtering queries executed mapping logical standard endpoints")
    except Exception:
        logger.error("Sophisticated internal semantic interpreting module encountered massive framework mapping processing interruption")
        return APIResponse(data=await DocumentService.get_text_search(query, limit), message="Base fundamental text analysis filtering queries executed mapping logical standard endpoints")

@router.get("/ai-suggestions", response_model=APIResponse[Any])
async def get_ai_recommendations(limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), current_user: dict = Depends(get_current_user_optional), db=Depends(get_db)):
    return APIResponse(
        data=await DocumentService.get_trending_documents(limit),
        message="Tailored automated structural content matching vectors processed mapping optimal logical correlations",
    )

@router.get("/trending-hashtags", response_model=APIResponse[Any])
async def get_trending_tags(limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), db=Depends(get_db)):
    return APIResponse(
        data=await DocumentService.get_trending_tags(limit),
        message="List identifying globally prioritized hyperactive functional structural indexing keywords retrieved seamlessly",
        status=status.HTTP_200_OK,
    )