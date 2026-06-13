from core.config import settings
from datetime import datetime, timezone
from typing import Any, List, Optional

from bson import ObjectId
from core.database import db_client
from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB
from fastapi import (
    APIRouter,
    Body,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from pydantic import BaseModel
from src.router.dependency_router import (
    get_current_user,
    get_current_user_optional,
    get_db,
    require_role,
)
from src.schemas.document_schema import (
    CoauthorInviteRequest,
    DocumentContentUpdate,
    DocumentCreate,
    DocumentPasswordRequest,
    DocumentResponse,
    DocumentUpdate,
)
from src.schemas.series_schema import SeriesCreateRequest, SeriesResponse
from src.services.document_service import DocumentService
from src.services.series_service import SeriesService

router = APIRouter(prefix="/document")


@router.post("", response_model=APIResponse[DocumentResponse])
async def create_document(
    doc_in: DocumentCreate,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])),
) -> Any:
    return APIResponse(
        data=await DocumentService.create_document(doc_in, current_user),
        message="Đã tạo tài liệu mới",
        status=status.HTTP_201_CREATED,
    )


@router.put("/{document_id}/content", response_model=APIResponse[DocumentResponse])
async def update_document_content(
    document_id: str,
    content_in: DocumentContentUpdate,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])),
) -> Any:
    return APIResponse(
        data=await DocumentService.update_document_content(
            document_id, content_in, current_user
        ),
        message="Đã cập nhật nội dung tài liệu",
        status=status.HTTP_200_OK,
    )


@router.put("/{document_id}", response_model=APIResponse[DocumentResponse])
async def update_document(
    document_id: str,
    doc_update: DocumentUpdate,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])),
) -> Any:
    return APIResponse(
        data=await DocumentService.update_document(
            document_id, doc_update, current_user
        ),
        message="Đã cập nhật thông tin tài liệu",
        status=status.HTTP_200_OK,
    )


@router.get("", response_model=APIResponse[List[DocumentResponse]])
async def list_documents(
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    cursor: Optional[str] = None,
    q: Optional[str] = None,
    sort_by: str = "latest",
    category: Optional[str] = None,
    tag: Optional[str] = None,
) -> Any:
    return APIResponse(
        data=await DocumentService.list_documents(
            limit, cursor, q, sort_by, category, tag
        ),
        message="Đã tải danh sách tài liệu",
        status=status.HTTP_200_OK,
    )


class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None


@router.get(
    "/thu-muc",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def get_folders(
    parent_id: Optional[str] = None, current_user: UserInDB = Depends(get_current_user)
):
    db = db_client.mongodb.get_default_database()
    query = {"author_id": str(current_user.id)}
    if parent_id:
        query["parent_id"] = parent_id
    cursor = db["workspace_folders"].find(query).sort("created_at", 1)
    folders = await cursor.to_list(length=100)
    for f in folders:
        f["_id"] = str(f["_id"])
    return APIResponse(data=folders, message="Đã tải danh sách thư mục")


@router.post(
    "/thu-muc",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def create_folder(
    req: FolderCreate, current_user: UserInDB = Depends(get_current_user)
):
    db = db_client.mongodb.get_default_database()
    folder_doc = {
        "name": req.name,
        "parent_id": req.parent_id,
        "author_id": str(current_user.id),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    res = await db["workspace_folders"].insert_one(folder_doc)
    folder_doc["_id"] = str(res.inserted_id)
    return APIResponse(data=folder_doc, message="Đã tạo thư mục")


@router.delete(
    "/thu-muc/{folder_id}",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def delete_folder(
    folder_id: str, current_user: UserInDB = Depends(get_current_user)
):
    db = db_client.mongodb.get_default_database()
    folder = await db["workspace_folders"].find_one(
        {"_id": ObjectId(folder_id), "author_id": str(current_user.id)}
    )
    if not folder:
        raise HTTPException(status_code=404, detail="Không tìm thấy thư mục")
    await db["workspace_folders"].delete_one({"_id": ObjectId(folder_id)})
    await db["documents"].update_many(
        {"folder_id": folder_id}, {"$unset": {"folder_id": ""}}
    )
    return APIResponse(data={"deleted": True}, message="Đã xóa thư mục")


@router.get(
    "/personal",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def get_my_documents(
    q: Optional[str] = None,
    cursor: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentService.get_my_documents(current_user, q, cursor, limit),
        message="Đã tải danh sách tài liệu cá nhân",
    )


@router.get(
    "/trash",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def get_trash(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.get_trash(current_user),
        message="Đã tải danh sách thùng rác",
    )


@router.get("/{document_id}", response_model=APIResponse[DocumentResponse])
async def get_document_by_id(
    document_id: str,
    password: Optional[str] = Header(None, alias="x-document-password"),
    current_user: UserInDB = Depends(get_current_user_optional),
) -> Any:
    return APIResponse(
        data=await DocumentService.get_document_by_id(
            document_id, current_user, password
        ),
        message="Đã tải thông tin tài liệu",
        status=status.HTTP_200_OK,
    )


@router.get("/d/{slug}", response_model=APIResponse[DocumentResponse])
async def get_document_by_slug(
    slug: str, current_user: UserInDB = Depends(get_current_user_optional)
) -> Any:
    return APIResponse(
        data=await DocumentService.get_document_by_slug(slug, current_user),
        message="Đã tải tài liệu theo đường dẫn",
        status=status.HTTP_200_OK,
    )


@router.get("/preview/{slug}", response_model=APIResponse[Any])
async def get_document_preview(slug: str):
    return APIResponse(
        data=await DocumentService.get_document_preview(slug),
        message="Đã tải bản xem trước tài liệu",
    )


@router.get(
    "/document-series/personal",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def get_my_series(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await SeriesService.get_my_series(current_user),
        message="Đã tải danh sách chuỗi tài liệu",
    )


@router.get("/document-series/{series_id}", response_model=APIResponse[Any])
async def get_series_by_id(series_id: str):
    return APIResponse(
        data=await SeriesService.get_series_by_id(series_id),
        message="Đã tải chi tiết chuỗi tài liệu",
    )


@router.post(
    "/document-series",
    response_model=APIResponse[Any],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def create_series(
    req: SeriesCreateRequest, current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(
        data=await SeriesService.create_series(req.model_dump(), current_user),
        message="Đã tạo chuỗi tài liệu mới",
        status=status.HTTP_201_CREATED,
    )


@router.put(
    "/document-series/{series_id}",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def update_series(
    series_id: str,
    req: SeriesCreateRequest,
    current_user: UserInDB = Depends(get_current_user),
):
    return APIResponse(
        data=await SeriesService.update_series(
            series_id, req.model_dump(), current_user
        ),
        message="Đã cập nhật chuỗi tài liệu",
    )


@router.delete(
    "/document-series/{series_id}",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def delete_series(
    series_id: str, current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(
        data=await SeriesService.delete_series(series_id, current_user),
        message="Đã xóa chuỗi tài liệu",
    )


@router.patch(
    "/document-series/{series_id}/document",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def reorder_series_documents(
    series_id: str,
    document_ids: List[str],
    current_user: UserInDB = Depends(get_current_user),
):
    return APIResponse(
        data=await SeriesService.reorder_series_documents(
            series_id, document_ids, current_user
        ),
        message="Đã sắp xếp lại thứ tự tài liệu",
    )


@router.post(
    "/{document_id}/document-series/{series_id}",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def link_series(
    document_id: str, series_id: str, current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(
        data=await SeriesService.link_series(document_id, series_id, current_user),
        message="Đã thêm tài liệu vào chuỗi",
        status=200,
    )


@router.delete(
    "/{document_id}",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def soft_delete_document(
    document_id: str, current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(
        data=await DocumentService.soft_delete_document(document_id, current_user),
        message="Đã chuyển tài liệu vào thùng rác",
    )


@router.post(
    "/{document_id}/restore",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def restore_document(
    document_id: str, current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(
        data=await DocumentService.restore_document(document_id, current_user),
        message="Đã khôi phục tài liệu",
    )


@router.post(
    "/{document_id}/bao-ve",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def set_document_password(
    document_id: str,
    req: DocumentPasswordRequest,
    current_user: UserInDB = Depends(get_current_user),
):
    return APIResponse(
        data=await DocumentService.set_document_password(
            document_id, req.password, current_user
        ),
        message="Đã thiết lập mật khẩu bảo vệ tài liệu",
    )


@router.get(
    "/{document_id}/nhat-ky-hoat-dong",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def get_document_audit_logs(
    document_id: str, current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(
        data=await DocumentService.get_document_audit_logs(document_id, current_user),
        message="Đã tải nhật ký hoạt động tài liệu",
    )


@router.post(
    "/{document_id}/star",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def toggle_star_document(
    document_id: str, current_user: UserInDB = Depends(get_current_user)
):
    db = db_client.mongodb.get_default_database()
    doc = await db["documents"].find_one(
        {"_id": document_id, "author_id": str(current_user.id)}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
    current_starred = doc.get("is_starred", False)
    await db["documents"].update_one(
        {"_id": document_id}, {"$set": {"is_starred": not current_starred}}
    )
    return APIResponse(
        data={"starred": not current_starred}, message="Đã đánh dấu sao tài liệu"
    )


@router.post(
    "/{document_id}/chuyen-nhuong",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def transfer_document(
    document_id: str,
    new_owner_id: str = Query(...),
    current_user: UserInDB = Depends(get_current_user),
):
    db = db_client.mongodb.get_default_database()
    doc = await db["documents"].find_one(
        {"_id": document_id, "author_id": str(current_user.id)}
    )
    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy tài liệu hoặc bạn không hiện có quyền",
        )
    import httpx

    target = None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.PROVISION_URL}/user/{new_owner_id}",
                timeout=settings.DEFAULT_HTTP_TIMEOUT,
            )
            if resp.status_code == 200:
                target = resp.json().get("data")
    except Exception:
        pass
    if not target:
        raise HTTPException(
            status_code=404, detail="Không tìm thấy người để chuyển nhượng"
        )
    await db["documents"].update_one(
        {"_id": document_id},
        {"$set": {"author_id": new_owner_id, "updated_at": datetime.now(timezone.utc)}},
    )
    return APIResponse(
        data={"status": "transferred", "new_owner_id": new_owner_id},
        message="Đã chuyển nhượng tài liệu",
    )


@router.get("/{document_id}/analyze", response_model=APIResponse[Any])
async def get_document_analytics(
    document_id: str, current_user: UserInDB = Depends(get_current_user)
):
    db = db_client.mongodb.get_default_database()
    doc = await db["documents"].find_one({"_id": document_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
    views = doc.get("views", 0)
    content = doc.get("content", "")
    total_words = len(content.split()) if content else 0
    avg_read_time_min = max(1, total_words // 200)
    comment_count = await db["comments"].count_documents(
        {"item_id": document_id, "item_type": "document"}
    )
    bookmark_count = await db["bookmarks"].count_documents({"document_id": document_id})
    review_pipeline = [
        {"$match": {"document_id": document_id}},
        {
            "$group": {
                "_id": None,
                "avg_rating": {"$avg": "$rating"},
                "count": {"$sum": 1},
            }
        },
    ]
    review_stats = await db["reviews"].aggregate(review_pipeline).to_list(length=1)
    avg_rating = review_stats[0]["avg_rating"] if review_stats else 0
    review_count = review_stats[0]["count"] if review_stats else 0
    purchase_count = await db["transactions"].count_documents(
        {"reference_id": document_id, "type": {"$in": ["purchase", "receive"]}}
    )
    return APIResponse(
        data={
            "views": views,
            "avg_read_time": f"{avg_read_time_min} phút",
            "avg_read_time_min": avg_read_time_min,
            "total_words": total_words,
            "saves": bookmark_count,
            "comments": comment_count,
            "reviews": review_count,
            "avg_rating": round(avg_rating, 1) if avg_rating else 0,
            "purchases": purchase_count,
        },
        message="Đã tải phân tích độc giả",
    )


@router.get("/{document_id}/academic-metrics", response_model=APIResponse[Any])
async def get_document_academic(
    document_id: str, current_user: UserInDB = Depends(get_current_user)
):
    db = db_client.mongodb.get_default_database()
    doc = await db["documents"].find_one({"_id": document_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
    content = doc.get("content", "")
    word_count = len(content.split()) if content else 0
    sentences = (
        content.count("") + content.count("!") + content.count("?") if content else 0
    )
    avg_sentence_len = round(word_count / max(sentences, 1), 1)
    readability_score = max(0, min(100, 100 - (avg_sentence_len - 15) * 3))
    return APIResponse(
        data={
            "word_count": word_count,
            "sentence_count": sentences,
            "avg_sentence_length": avg_sentence_len,
            "readability_score": round(readability_score, 1),
            "content_format": doc.get("content_format", "html"),
        },
        message="Đã tải chỉ số học thuật",
    )


class DRMSettingsUpdate(BaseModel):
    disable_copy: bool = False
    hide_from_search: bool = False


@router.put(
    "/{document_id}/drm",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def update_drm_settings(
    document_id: str,
    req: DRMSettingsUpdate,
    current_user: UserInDB = Depends(get_current_user),
):
    result = await DocumentService.update_document(
        document_id,
        DocumentUpdate(
            drm_settings={
                "disable_copy": req.disable_copy,
                "hide_from_search": req.hide_from_search,
            }
        ),
        current_user,
    )
    return APIResponse(data=result, message="Đã cập nhật cài đặt bảo vệ bản quyền")


class TagsUpdate(BaseModel):
    tags: List[str]


@router.put(
    "/{document_id}/tags",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def update_tags(
    document_id: str,
    req: TagsUpdate,
    current_user: UserInDB = Depends(get_current_user),
):
    result = await DocumentService.update_document(
        document_id, DocumentUpdate(tags=req.tags), current_user
    )
    return APIResponse(data=result, message="Đã cập nhật thẻ tài liệu")


class ScheduleUpdate(BaseModel):
    publish_at: str


@router.put(
    "/{document_id}/hen-gio",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def schedule_publish(
    document_id: str,
    req: ScheduleUpdate,
    current_user: UserInDB = Depends(get_current_user),
):
    result = await DocumentService.update_document(
        document_id,
        DocumentUpdate(publish_at=req.publish_at, scheduled_publish_at=req.publish_at),
        current_user,
    )
    return APIResponse(data=result, message="Đã lên lịch xuất bản")


class NSFWUpdate(BaseModel):
    is_nsfw: bool


@router.put(
    "/{document_id}/nsfw",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def update_nsfw(
    document_id: str,
    req: NSFWUpdate,
    current_user: UserInDB = Depends(get_current_user),
):
    result = await DocumentService.update_document(
        document_id, DocumentUpdate(is_nsfw=req.is_nsfw), current_user
    )
    return APIResponse(data=result, message="Đã cập nhật giới hạn độ tuổi")


class BroadcastRequest(BaseModel):
    message: str


@router.post(
    "/{document_id}/notification",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def broadcast_notification(
    document_id: str,
    req: BroadcastRequest,
    current_user: UserInDB = Depends(get_current_user),
):
    db = db_client.mongodb.get_default_database()
    doc = await db["documents"].find_one(
        {"_id": document_id, "author_id": str(current_user.id)}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")

    libraries = (
        await db["libraries"].find({"document_id": document_id}).to_list(length=1000)
    )

    import httpx
    from core.config import settings

    if settings.SIGNAL_URL:
        async with httpx.AsyncClient() as client:
            for lib in libraries:
                try:
                    await client.post(
                        f"{settings.SIGNAL_URL}/notification/trigger",
                        json={
                            "target_user_id": lib["user_id"],
                            "title": "Thông báo từ tác giả của '{doc.get('title', 'Tài liệu')}'",
                            "body": req.message,
                            "type": "SYSTEM",
                        },
                        timeout=settings.DEFAULT_HTTP_TIMEOUT,
                    )
                except Exception as e:
                    pass
    return APIResponse(
        data={"sent": True, "message": req.message},
        message="Đã gửi thông báo đến độc giả",
    )


@router.post("/{document_id}/unlock", response_model=APIResponse[Any])
async def unlock_document(
    document_id: str,
    password: str = Body(..., embed=True),
    current_user: UserInDB = Depends(get_current_user_optional),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentService.get_document_by_id(
            document_id, current_user, password
        ),
        message="Đã mở khóa tài liệu",
        status=status.HTTP_200_OK,
    )
