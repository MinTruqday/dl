from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from src.core.logging_route import LoggingRoute
from src.core.dependency import verify_internal_token
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database

router = APIRouter(route_class=LoggingRoute)

@router.post(
    "/noi-bo/truy-cap", dependencies=[Depends(verify_internal_token)], include_in_schema=False
)
async def get_internal_document(req: dict):
    document_id = str(req.get("document_id", ""))
    user_id = str(req.get("user_id", ""))
    edit = bool(req.get("edit", False))
    is_admin = bool(req.get("is_admin", False))
    access = [
        {"creator_id": user_id},
        {"coauthors": user_id},
        {"collaborators.user_id": user_id},
        {"shared_with.user_id": user_id},
    ]
    if not edit:
        access.append({"visibility": "public", "status": "published"})
    query = {"_id": document_id}
    if not is_admin:
        query["$or"] = access
    document = await database.mongodb[settings.CONTENT_DB_NAME].documents.find_one(query)
    if not document:
        raise HTTPException(
            status_code=404, detail="Không tìm thấy tài liệu hoặc thiếu quyền truy cập"
        )
    document["_id"] = str(document["_id"])
    return {"data": document}

@router.post(
    "/noi-bo/cong-viec", dependencies=[Depends(verify_internal_token)], include_in_schema=False
)
async def update_document_job(req: dict):
    action = str(req.get("action", ""))
    document_id = str(req.get("document_id", ""))
    creator_id = str(req.get("creator_id", ""))
    job_id = str(req.get("job_id", ""))
    now = datetime.now(timezone.utc)
    documents = database.mongodb[settings.CONTENT_DB_NAME].documents
    if action == "get_creator":
        row = await documents.find_one({"_id": document_id}, {"creator_id": 1})
        return {"data": {"exists": bool(row), "creator_id": str((row or {}).get("creator_id", ""))}}
    if action == "compile_complete":
        result = await documents.update_one(
            {"_id": document_id, "creator_id": creator_id},
            {
                "$set": {
                    "compiled_file_url": req["file_url"],
                    "compile_status": "completed",
                    "compiled_at": now,
                    "updated_at": now,
                },
                "$unset": {"compile_error": ""},
            },
        )
        return {"data": {"updated": result.modified_count == 1}}
    if action == "publish_complete":
        result = await documents.update_one(
            {
                "_id": document_id,
                "creator_id": creator_id,
                "publication_job_id": job_id,
                "status": "processing_publish",
                "is_deleted": {"$ne": True},
            },
            {
                "$set": {"status": "published", "published_at": now, "updated_at": now},
                "$unset": {
                    "publication_job_id": "",
                    "publication_error": "",
                    "scheduled_publish_at": "",
                    "publish_at": "",
                },
            },
        )
        return {"data": {"updated": result.modified_count == 1}}
    return {"data": {"updated": False}}
