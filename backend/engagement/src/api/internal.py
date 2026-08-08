from fastapi import APIRouter, Depends

from src.core.dependency import verify_internal_token
from src.core.infrastructure.mongo import mongo


router = APIRouter(prefix="/tuong-tac/noi-bo")


@router.post(
    "/thong-ke",
    dependencies=[Depends(verify_internal_token)],
    include_in_schema=False,
)
async def get_document_engagement_stats(req: dict):
    document_id = str(req.get("document_id", ""))
    saves = await mongo.count_documents(
        "user_content_profiles",
        {"bookmarks": document_id},
    )
    reads = await mongo.count_documents(
        "reading_history",
        {"document_id": document_id},
    )
    highlights = await mongo.count_documents(
        "highlights",
        {"document_id": document_id},
    )
    return {
        "data": {
            "saves": saves,
            "reads": reads,
            "highlights": highlights,
        }
    }
