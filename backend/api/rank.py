from typing import Any
from fastapi import APIRouter, Depends, Query, status
from core.response import APIResponse
from services.rank import RankService
from services.document import DocumentService
from core.database import db_client

router = APIRouter(prefix="/xep-hang")

async def populate_author(doc: dict) -> dict:
    if not doc or "author_id" not in doc:
        return doc
    db = db_client.mongodb.get_default_database()
    author = await db["users"].find_one({"_id": doc["author_id"]})
    if author:
        doc["author"] = {
            "_id": str(author["_id"]),
            "full_name": author.get("full_name") or author.get("username") or "Tác giả ẩn danh",
            "slug": author.get("slug", "")
        }
    return doc

@router.get("", response_model=APIResponse[Any])
async def get_leaderboard(limit: int = Query(5, ge=1, le=50)):
    trending_docs = await DocumentService.get_trending_documents(limit)
    trending_docs_populated = [await populate_author(d) for d in trending_docs]

    rated_docs = await DocumentService.list_documents(limit=limit, cursor=None, q=None, sort_by="rating")
    rated_docs_populated = [await populate_author(d) for d in rated_docs]

    top_authors = await RankService.get_featured_authors(limit)
    
    data = {
        "top_documents_by_views": trending_docs_populated,
        "top_documents_by_rating": rated_docs_populated,
        "top_authors": top_authors
    }
    return APIResponse(data=data, message="Lấy bảng xếp hạng thành công", status=status.HTTP_200_OK)

@router.get("/dong-gop", response_model=APIResponse[Any])
async def get_contribution_ranking(limit: int = Query(5, ge=1, le=50)):
    return APIResponse(data=await RankService.get_contribution_ranking(limit), message="Lấy bảng xếp hạng đóng góp thành công", status=status.HTTP_200_OK)

@router.get("/doc-gia", response_model=APIResponse[Any])
async def get_reader_ranking(limit: int = Query(5, ge=1, le=50)):
    return APIResponse(data=await RankService.get_reader_ranking(limit), message="Lấy bảng xếp hạng độc giả thành công", status=status.HTTP_200_OK)

@router.get("/tac-gia-noi-bat", response_model=APIResponse[Any])
async def get_featured_authors(limit: int = Query(10, ge=1, le=50)):
    return APIResponse(data=await RankService.get_featured_authors(limit), message="Lấy danh sách tác giả nổi bật thành công", status=status.HTTP_200_OK)
