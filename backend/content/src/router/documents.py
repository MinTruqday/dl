import httpx
from datetime import datetime, timezone
from typing import Any, List, Optional
from bson import ObjectId
from core.config import settings
from core.database import db_client
from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status, Body
from pydantic import BaseModel
from src.dependencies import get_current_user, get_current_user_optional, get_db, require_role
from src.schemas.documents import DocumentContentUpdate, DocumentCreate, DocumentPasswordRequest, DocumentResponse, DocumentUpdate
from src.services.documents import DocumentService

router = APIRouter(prefix="/documents")

class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None

class DRMSettingsUpdate(BaseModel):
    disable_copy: bool = False
    hide_from_search: bool = False

class TagsUpdate(BaseModel):
    tags: List[str]

class ScheduleUpdate(BaseModel):
    publish_at: str

@router.post("", response_model=APIResponse[DocumentResponse])
async def create_document(doc_in: DocumentCreate, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))) -> Any:
    return APIResponse(
        data=await DocumentService.create_document(doc_in, current_user),
        message="New digital document has been successfully created and added to central system repository",
        status=status.HTTP_201_CREATED,
    )

@router.put("/{document_id}/content", response_model=APIResponse[DocumentResponse])
async def update_document_content(document_id: str, content_in: DocumentContentUpdate, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))) -> Any:
    return APIResponse(
        data=await DocumentService.update_document_content(document_id, content_in, current_user),
        message="Primary content of specified digital document has been successfully modified and securely saved",
        status=status.HTTP_200_OK,
    )

@router.put("/{document_id}", response_model=APIResponse[DocumentResponse])
async def update_document(document_id: str, doc_update: DocumentUpdate, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))) -> Any:
    return APIResponse(
        data=await DocumentService.update_document(document_id, doc_update, current_user),
        message="Descriptive metadata associated with specified digital document has been successfully updated",
        status=status.HTTP_200_OK,
    )

@router.get("", response_model=APIResponse[List[DocumentResponse]])
async def list_documents(limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), cursor: Optional[str] = None, q: Optional[str] = None, sort_by: str = "latest", category: Optional[str] = None, tag: Optional[str] = None) -> Any:
    return APIResponse(
        data=await DocumentService.list_documents(limit, cursor, q, sort_by, category, tag),
        message="Requested catalog of active digital documents has been successfully retrieved from system database",
        status=status.HTTP_200_OK,
    )

@router.get("/folders", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def get_folders(parent_id: Optional[str] = None, current_user: UserInDB = Depends(get_current_user)):
    db = db_client.mongodb.get_default_database()
    query = {"creator_id": str(current_user.id)}
    if parent_id: query["parent_id"] = parent_id
    folders = await db["workspace_folders"].find(query).sort("created_at", 1).to_list(length=100)
    for f in folders: f["_id"] = str(f["_id"])
    return APIResponse(data=folders, message="Hierarchical operational folder structure has been successfully retrieved from personal workspace")

@router.post("/folders", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def create_folder(req: FolderCreate, current_user: UserInDB = Depends(get_current_user)):
    db = db_client.mongodb.get_default_database()
    folder_doc = {"name": req.name, "parent_id": req.parent_id, "creator_id": str(current_user.id), "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)}
    res = await db["workspace_folders"].insert_one(folder_doc)
    folder_doc["_id"] = str(res.inserted_id)
    return APIResponse(data=folder_doc, message="New organizational structural folder has been successfully provisioned within designated active workspace")

@router.delete("/folders/{folder_id}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def delete_folder(folder_id: str, current_user: UserInDB = Depends(get_current_user)):
    db = db_client.mongodb.get_default_database()
    if not await db["workspace_folders"].find_one({"_id": ObjectId(folder_id), "creator_id": str(current_user.id)}):
        raise HTTPException(status_code=404, detail="System was unable to locate specified organizational folder within current active workspace")
    await db["workspace_folders"].delete_one({"_id": ObjectId(folder_id)})
    await db["documents"].update_many({"folder_id": folder_id}, {"$unset": {"folder_id": ""}})
    return APIResponse(data={"deleted": True}, message="Specified organizational directory folder has been permanently removed from active system workspace")

@router.get("/personal", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def get_my_documents(q: Optional[str] = None, cursor: Optional[str] = None, limit: int = Query(50, ge=1, le=100), current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await DocumentService.get_my_documents(current_user, q, cursor, limit), message="Collection of personally authored digital documents has been successfully retrieved internally")

@router.get("/trash", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def get_trash(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await DocumentService.get_trash(current_user), message="Contents of volatile temporary deletion bin have been successfully retrieved from database")

@router.get("/{document_id}", response_model=APIResponse[DocumentResponse])
async def get_document_by_id(document_id: str, password: Optional[str] = Header(None, alias="x-document-password"), current_user: UserInDB = Depends(get_current_user_optional)) -> Any:
    return APIResponse(data=await DocumentService.get_document_by_id(document_id, current_user, password), message="Detailed structural information mapping specified digital document successfully retrieved securely", status=status.HTTP_200_OK)

@router.get("/d/{slug}", response_model=APIResponse[DocumentResponse])
async def get_document_by_slug(slug: str, current_user: UserInDB = Depends(get_current_user_optional)) -> Any:
    return APIResponse(data=await DocumentService.get_document_by_slug(slug, current_user), message="Digital document corresponding to specified navigational routing path successfully retrieved internally", status=status.HTTP_200_OK)

@router.get("/preview/{slug}", response_model=APIResponse[Any])
async def get_document_preview(slug: str):
    return APIResponse(data=await DocumentService.get_document_preview(slug), message="Publicly accessible structural preview of specified digital document successfully retrieved dynamically")

@router.delete("/{document_id}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def soft_delete_document(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await DocumentService.soft_delete_document(document_id, current_user), message="Specified digital document has been successfully moved securely into temporary deletion bin")

@router.post("/{document_id}/restore", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def restore_document(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await DocumentService.restore_document(document_id, current_user), message="Specified digital document successfully recovered restoring active status from temporary deletion bin")

@router.post("/{document_id}/protect", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def set_document_password(document_id: str, req: DocumentPasswordRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await DocumentService.set_document_password(document_id, req.password, current_user), message="Cryptographic access protection password shielding specified document successfully configured structurally")

@router.get("/{document_id}/activity-log", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def get_document_audit_logs(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await DocumentService.get_document_audit_logs(document_id, current_user), message="Comprehensive administrative tracking activity log mapping specified document successfully retrieved")

@router.post("/{document_id}/star", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def toggle_star_document(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    db = db_client.mongodb.get_default_database()
    doc = await db["documents"].find_one({"_id": document_id, "creator_id": str(current_user.id)})
    if not doc: raise HTTPException(status_code=404, detail="System essentially failed uncovering designated active file updating secure internal repository")
    current_starred = doc.get("is_starred", False)
    await db["documents"].update_one({"_id": document_id}, {"$set": {"is_starred": not current_starred}})
    return APIResponse(data={"starred": not current_starred}, message="Prioritization logical status tracking specified digital document successfully toggled dynamically")

@router.post("/{document_id}/transfer", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def transfer_document(document_id: str, new_owner_id: str = Query(...), current_user: UserInDB = Depends(get_current_user)):
    db = db_client.mongodb.get_default_database()
    if not await db["documents"].find_one({"_id": document_id, "creator_id": str(current_user.id)}):
        raise HTTPException(status_code=404, detail="System failed pinpointing required structural document avoiding executing restricted ownership transfer")
    target = None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{settings.PROVISION_URL}/users/{new_owner_id}", timeout=settings.DEFAULT_HTTP_TIMEOUT)
            if resp.status_code == 200: target = resp.json().get("data")
    except Exception: pass
    if not target: raise HTTPException(status_code=404, detail="Target user account specified executing operational ownership transfer strictly unavailable")
    await db["documents"].update_one({"_id": document_id}, {"$set": {"creator_id": new_owner_id, "updated_at": datetime.now(timezone.utc)}})
    return APIResponse(data={"status": "transferred", "new_owner_id": new_owner_id}, message="Administrative ownership functional rights attached specified document successfully transferred reliably")

@router.get("/{document_id}/analytics", response_model=APIResponse[Any])
async def get_document_analytics(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    db = db_client.mongodb.get_default_database()
    doc = await db["documents"].find_one({"_id": document_id})
    if not doc: raise HTTPException(status_code=404, detail="System was entirely unable to accurately uncover requested internal structural resource")
    views, content = doc.get("views", 0), doc.get("content", "")
    total_words = len(content.split()) if content else 0
    avg_read_time_min = max(1, total_words // 200)
    comment_count = await db["comments"].count_documents({"item_id": document_id, "item_type": "document"})
    bookmark_count = await db["bookmarks"].count_documents({"document_id": document_id})
    review_stats = await db["reviews"].aggregate([{"$match": {"document_id": document_id}}, {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}, "count": {"$sum": 1}}}]).to_list(length=1)
    avg_rating = review_stats[0]["avg_rating"] if review_stats else 0
    purchase_count = await db["transactions"].count_documents({"reference_id": document_id, "type": {"$in": ["purchase", "receive"]}})
    return APIResponse(data={"views": views, "avg_read_time": f"{avg_read_time_min} minutes", "avg_read_time_min": avg_read_time_min, "total_words": total_words, "saves": bookmark_count, "comments": comment_count, "reviews": review_stats[0]["count"] if review_stats else 0, "avg_rating": round(avg_rating, 1) if avg_rating else 0, "purchases": purchase_count}, message="Comprehensive reader engagement analytical metrics mapping designated document successfully calculated")

@router.get("/{document_id}/academic-index", response_model=APIResponse[Any])
async def get_document_academic(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    db = db_client.mongodb.get_default_database()
    doc = await db["documents"].find_one({"_id": document_id})
    if not doc: raise HTTPException(status_code=404, detail="System was entirely unable to accurately uncover requested internal structural resource")
    content = doc.get("content", "")
    word_count = len(content.split()) if content else 0
    sentences = content.count(".") + content.count("!") + content.count("?") if content else 0
    avg_sentence_len = round(word_count / max(sentences, 1), 1)
    return APIResponse(data={"word_count": word_count, "sentence_count": sentences, "avg_sentence_length": avg_sentence_len, "readability_score": round(max(0, min(100, 100 - (avg_sentence_len - 15) * 3)), 1), "content_format": doc.get("content_format", "html")}, message="Academic complexity linguistic readability metrics evaluating designated document successfully extracted")

@router.put("/{document_id}/drm", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def update_drm_settings(document_id: str, req: DRMSettingsUpdate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await DocumentService.update_document(document_id, DocumentUpdate(drm_settings={"disable_copy": req.disable_copy, "hide_from_search": req.hide_from_search}), current_user), message="Digital rights management copyright protection systemic configurations successfully applied internally")

@router.put("/{document_id}/tags", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def update_tags(document_id: str, req: TagsUpdate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await DocumentService.update_document(document_id, DocumentUpdate(tags=req.tags), current_user), message="Thematic categorization metadata tags logically assigned specified digital document updated functionally")

@router.put("/{document_id}/schedule", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def schedule_publish(document_id: str, req: ScheduleUpdate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await DocumentService.update_document(document_id, DocumentUpdate(publish_at=req.publish_at, scheduled_publish_at=req.publish_at), current_user), message="Automated sequential publication release schedule specified digital document functionally orchestrated reliably")

@router.post("/{document_id}/unlock", response_model=APIResponse[Any])
async def unlock_document(document_id: str, password: str = Body(..., embed=True), current_user: UserInDB = Depends(get_current_user_optional), db=Depends(get_db)):
    return APIResponse(data=await DocumentService.get_document_by_id(document_id, current_user, password), message="Cryptographic access protection reliably bypassed verifying provided operational security credentials completely", status=status.HTTP_200_OK)