import httpx
from datetime import datetime, timezone
from typing import Any, List, Optional
from bson import ObjectId
from core.config import settings
from core.database import db_client
from core.response import APIResponse
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status, Body
from pydantic import BaseModel
from core.dependency import get_current_user, get_current_user_optional, get_db, require_role
from src.schemas.documents import DocumentContentUpdate, DocumentCreate, DocumentPasswordRequest, DocumentResponse, DocumentUpdate
from src.services.documents import DocumentService

router = APIRouter(prefix="/tai-lieu")

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
async def create_document(doc_in: DocumentCreate, current_user: dict = Depends(require_role(["author", "admin"]))) -> Any:
    return APIResponse(
        data=await DocumentService.create_document(doc_in, current_user),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=status.HTTP_201_CREATED,
    )

@router.put("/{document_id}/noi-dung", response_model=APIResponse[DocumentResponse])
async def update_document_content(document_id: str, content_in: DocumentContentUpdate, current_user: dict = Depends(require_role(["author", "admin"]))) -> Any:
    return APIResponse(
        data=await DocumentService.update_document_content(document_id, content_in, current_user),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=status.HTTP_200_OK,
    )

@router.put("/{document_id}", response_model=APIResponse[DocumentResponse])
async def update_document(document_id: str, doc_update: DocumentUpdate, current_user: dict = Depends(require_role(["author", "admin"]))) -> Any:
    return APIResponse(
        data=await DocumentService.update_document(document_id, doc_update, current_user),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=status.HTTP_200_OK,
    )

@router.get("", response_model=APIResponse[List[DocumentResponse]])
async def list_documents(limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), cursor: Optional[str] = None, q: Optional[str] = None, sort_by: str = "latest", category: Optional[str] = None, tag: Optional[str] = None) -> Any:
    return APIResponse(
        data=await DocumentService.list_documents(limit, cursor, q, sort_by, category, tag),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=status.HTTP_200_OK,
    )

@router.get("/thu-muc", response_model=APIResponse[Any], dependencies=[Depends(require_role(["author", "admin"]))])
async def get_folders(parent_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    db = db_client.mongodb.get_default_database()
    query = {"creator_id": str(current_user.get("id"))}
    if parent_id: query["parent_id"] = parent_id
    folders = await db["workspace_folders"].find(query).sort("created_at", 1).to_list(length=100)
    for f in folders: f["_id"] = str(f["_id"])
    return APIResponse(data=folders, message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")

@router.post("/thu-muc", response_model=APIResponse[Any], dependencies=[Depends(require_role(["author", "admin"]))])
async def create_folder(req: FolderCreate, current_user: dict = Depends(get_current_user)):
    db = db_client.mongodb.get_default_database()
    folder_doc = {"name": req.name, "parent_id": req.parent_id, "creator_id": str(current_user.get("id")), "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)}
    res = await db["workspace_folders"].insert_one(folder_doc)
    folder_doc["_id"] = str(res.inserted_id)
    return APIResponse(data=folder_doc, message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")

@router.delete("/thu-muc/{folder_id}", response_model=APIResponse[Any], dependencies=[Depends(require_role(["author", "admin"]))])
async def delete_folder(folder_id: str, current_user: dict = Depends(get_current_user)):
    db = db_client.mongodb.get_default_database()
    if not await db["workspace_folders"].find_one({"_id": ObjectId(folder_id), "creator_id": str(current_user.get("id"))}):
        raise HTTPException(status_code=404, detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
    await db["workspace_folders"].delete_one({"_id": ObjectId(folder_id)})
    await db["documents"].update_many({"folder_id": folder_id}, {"$unset": {"folder_id": ""}})
    return APIResponse(data={"deleted": True}, message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")

@router.get("/ca-nhan", response_model=APIResponse[Any], dependencies=[Depends(require_role(["author", "admin"]))])
async def get_my_documents(q: Optional[str] = None, cursor: Optional[str] = None, limit: int = Query(50, ge=1, le=100), current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await DocumentService.get_my_documents(current_user, q, cursor, limit), message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")

@router.get("/thung-rac", response_model=APIResponse[Any], dependencies=[Depends(require_role(["author", "admin"]))])
async def get_trash(current_user: dict = Depends(get_current_user)):
    return APIResponse(data=await DocumentService.get_trash(current_user), message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")

@router.get("/{document_id}", response_model=APIResponse[DocumentResponse])
async def get_document_by_id(document_id: str, password: Optional[str] = Header(None, alias="x-document-password"), current_user: dict = Depends(get_current_user_optional)) -> Any:
    return APIResponse(data=await DocumentService.get_document_by_id(document_id, current_user, password), message="Khởi tạo AI thành công", status=status.HTTP_200_OK)

@router.get("/d/{slug}", response_model=APIResponse[DocumentResponse])
async def get_document_by_slug(slug: str, current_user: dict = Depends(get_current_user_optional)) -> Any:
    return APIResponse(data=await DocumentService.get_document_by_slug(slug, current_user), message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công", status=status.HTTP_200_OK)

@router.get("/xem-truoc/{slug}", response_model=APIResponse[Any])
async def get_document_preview(slug: str):
    return APIResponse(data=await DocumentService.get_document_preview(slug), message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")

@router.delete("/{document_id}", response_model=APIResponse[Any], dependencies=[Depends(require_role(["author", "admin"]))])
async def soft_delete_document(document_id: str, current_user: dict = Depends(get_current_user)):
    return APIResponse(data=await DocumentService.soft_delete_document(document_id, current_user), message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")

@router.post("/{document_id}/khoi-phuc", response_model=APIResponse[Any], dependencies=[Depends(require_role(["author", "admin"]))])
async def restore_document(document_id: str, current_user: dict = Depends(get_current_user)):
    return APIResponse(data=await DocumentService.restore_document(document_id, current_user), message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")

@router.post("/{document_id}/bao-ve", response_model=APIResponse[Any], dependencies=[Depends(require_role(["author", "admin"]))])
async def set_document_password(document_id: str, req: DocumentPasswordRequest, current_user: dict = Depends(get_current_user)):
    return APIResponse(data=await DocumentService.set_document_password(document_id, req.password, current_user), message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")

@router.get("/{document_id}/nhat-ky", response_model=APIResponse[Any], dependencies=[Depends(require_role(["author", "admin"]))])
async def get_document_audit_logs(document_id: str, current_user: dict = Depends(get_current_user)):
    return APIResponse(data=await DocumentService.get_document_audit_logs(document_id, current_user), message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")

@router.post("/{document_id}/gan-sao", response_model=APIResponse[Any], dependencies=[Depends(require_role(["author", "admin"]))])
async def toggle_star_document(document_id: str, current_user: dict = Depends(get_current_user)):
    db = db_client.mongodb.get_default_database()
    doc = await db["documents"].find_one({"_id": document_id, "creator_id": str(current_user.get("id"))})
    if not doc: raise HTTPException(status_code=404, detail="Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
    current_starred = doc.get("is_starred", False)
    await db["documents"].update_one({"_id": document_id}, {"$set": {"is_starred": not current_starred}})
    return APIResponse(data={"starred": not current_starred}, message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")

@router.post("/{document_id}/chuyen-khoan", response_model=APIResponse[Any], dependencies=[Depends(require_role(["author", "admin"]))])
async def transfer_document(document_id: str, new_owner_id: str = Query(...), current_user: dict = Depends(get_current_user)):
    db = db_client.mongodb.get_default_database()
    if not await db["documents"].find_one({"_id": document_id, "creator_id": str(current_user.get("id"))}):
        raise HTTPException(status_code=404, detail="Lỗi khi truy xuất tài liệu")
    target = None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{settings.MANAGEMENT_URL}/nguoi-dung/{new_owner_id}", timeout=settings.DEFAULT_HTTP_TIMEOUT)
            if resp.status_code == 200: target = resp.json().get("data")
    except Exception: pass
    if not target: raise HTTPException(status_code=404, detail="Lỗi xử lý tài khoản")
    await db["documents"].update_one({"_id": document_id}, {"$set": {"creator_id": new_owner_id, "updated_at": datetime.now(timezone.utc)}})
    return APIResponse(data={"status": "transferred", "new_owner_id": new_owner_id}, message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")

@router.get("/{document_id}/phan-tich", response_model=APIResponse[Any])
async def get_document_analytics(document_id: str, current_user: dict = Depends(get_current_user)):
    db = db_client.mongodb.get_default_database()
    doc = await db["documents"].find_one({"_id": document_id})
    if not doc: raise HTTPException(status_code=404, detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
    views, content = doc.get("views", 0), doc.get("content", "")
    total_words = len(content.split()) if content else 0
    avg_read_time_min = max(1, total_words // 200)
    comment_count = await db["comments"].count_documents({"item_id": document_id, "item_type": "document"})
    bookmark_count = await db["bookmarks"].count_documents({"document_id": document_id})
    review_stats = await db["reviews"].aggregate([{"$match": {"document_id": document_id}}, {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}, "count": {"$sum": 1}}}]).to_list(length=1)
    avg_rating = review_stats[0]["avg_rating"] if review_stats else 0
    purchase_count = await db["transactions"].count_documents({"reference_id": document_id, "type": {"$in": ["purchase", "receive"]}})
    return APIResponse(data={"views": views, "avg_read_time": f"{avg_read_time_min} minutes", "avg_read_time_min": avg_read_time_min, "total_words": total_words, "saves": bookmark_count, "comments": comment_count, "reviews": review_stats[0]["count"] if review_stats else 0, "avg_rating": round(avg_rating, 1) if avg_rating else 0, "purchases": purchase_count}, message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")

@router.get("/{document_id}/chi-so", response_model=APIResponse[Any])
async def get_document_academic(document_id: str, current_user: dict = Depends(get_current_user)):
    db = db_client.mongodb.get_default_database()
    doc = await db["documents"].find_one({"_id": document_id})
    if not doc: raise HTTPException(status_code=404, detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
    content = doc.get("content", "")
    word_count = len(content.split()) if content else 0
    sentences = content.count(".") + content.count("!") + content.count("?") if content else 0
    avg_sentence_len = round(word_count / max(sentences, 1), 1)
    return APIResponse(data={"word_count": word_count, "sentence_count": sentences, "avg_sentence_length": avg_sentence_len, "readability_score": round(max(0, min(100, 100 - (avg_sentence_len - 15) * 3)), 1), "content_format": doc.get("content_format", "html")}, message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")

@router.put("/{document_id}/drm", response_model=APIResponse[Any], dependencies=[Depends(require_role(["author", "admin"]))])
async def update_drm_settings(document_id: str, req: DRMSettingsUpdate, current_user: dict = Depends(get_current_user)):
    return APIResponse(data=await DocumentService.update_document(document_id, DocumentUpdate(drm_settings={"disable_copy": req.disable_copy, "hide_from_search": req.hide_from_search}), current_user), message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")

@router.put("/{document_id}/nhan-dan", response_model=APIResponse[Any], dependencies=[Depends(require_role(["author", "admin"]))])
async def update_tags(document_id: str, req: TagsUpdate, current_user: dict = Depends(get_current_user)):
    return APIResponse(data=await DocumentService.update_document(document_id, DocumentUpdate(tags=req.tags), current_user), message="Lỗi khi truy xuất tài liệu")

@router.put("/{document_id}/lich-trinh", response_model=APIResponse[Any], dependencies=[Depends(require_role(["author", "admin"]))])
async def schedule_publish(document_id: str, req: ScheduleUpdate, current_user: dict = Depends(get_current_user)):
    return APIResponse(data=await DocumentService.update_document(document_id, DocumentUpdate(publish_at=req.publish_at, scheduled_publish_at=req.publish_at), current_user), message="Lỗi khi truy xuất tài liệu")

@router.post("/{document_id}/mo-khoa-lai", response_model=APIResponse[Any])
async def unlock_document(document_id: str, password: str = Body(..., embed=True), current_user: dict = Depends(get_current_user_optional), db=Depends(get_db)):
    return APIResponse(data=await DocumentService.get_document_by_id(document_id, current_user, password), message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công", status=status.HTTP_200_OK)