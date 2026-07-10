from datetime import datetime, timezone
from typing import Any, List, Optional

from bson import ObjectId
from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel
from src.api.dependency import (
    get_current_user,
    get_current_user_optional,
    get_db,
    require_role,
)
from src.schemas.document import (
    DocumentContentUpdate,
    DocumentCreate,
    DocumentPasswordRequest,
    DocumentResponse,
    DocumentUpdate,
    FolderCreate,
    TagsUpdate,
    ScheduleUpdate,
)
from src.services.document import DocumentService

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(route_class=LoggingRoute, prefix="/tai-lieu")

@router.post("", response_model=APIResponse[DocumentResponse])
async def create_document(
    doc_in: DocumentCreate,
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN])),
) -> Any:
    return APIResponse(
        data=await DocumentService.create_document(doc_in, current_user),
        message="Khởi tạo tài liệu mới trên hệ thống hoàn tất",
        status=status.HTTP_201_CREATED,
    )

@router.put("/{document_id}/noi-dung", response_model=APIResponse[DocumentResponse])
async def update_document_content(
    document_id: str,
    content_in: DocumentContentUpdate,
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN])),
) -> Any:
    return APIResponse(
        data=await DocumentService.update_document_content(
            document_id, content_in, current_user
        ),
        message="Cập nhật dữ liệu nội dung tài liệu hoàn tất",
        status=status.HTTP_200_OK,
    )

@router.put("/{document_id}", response_model=APIResponse[DocumentResponse])
async def update_document(
    document_id: str,
    doc_update: DocumentUpdate,
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN])),
) -> Any:
    return APIResponse(
        data=await DocumentService.update_document(
            document_id, doc_update, current_user
        ),
        message="Cập nhật dữ liệu siêu dữ liệu (metadata) tài liệu hoàn tất",
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
        message="Trích xuất danh mục tài liệu hoàn tất",
        status=status.HTTP_200_OK,
    )

@router.get(
    "/thu-muc",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def get_folders(
    parent_id: Optional[str] = None, current_user: CurrentUser = Depends(get_current_user)
):
    folders = await DocumentService.get_folders(parent_id, current_user)
    return APIResponse(data=folders, message="Trích xuất cấu trúc cây thư mục hoàn tất")

@router.post(
    "/thu-muc",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def create_folder(
    req: FolderCreate, current_user: CurrentUser = Depends(get_current_user)
):
    folder_doc = await DocumentService.create_folder(req.name, req.parent_id, current_user)
    return APIResponse(data=folder_doc, message="Khởi tạo không gian thư mục làm việc mới hoàn tất")

@router.delete(
    "/thu-muc/{folder_id}",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def delete_folder(
    folder_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    res = await DocumentService.delete_folder(folder_id, current_user)
    return APIResponse(
        data=res, message="Thư mục và toàn bộ dữ liệu liên quan đã được xóa vĩnh viễn"
    )

@router.get(
    "/ca-nhan",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def get_my_documents(
    q: Optional[str] = None,
    cursor: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentService.get_my_documents(current_user, q, cursor, limit),
        message="Trích xuất danh sách tài liệu cá nhân hoàn tất",
    )

@router.get(
    "/thung-rac",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def get_trash(current_user: CurrentUser = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.get_trash(current_user),
        message="Trích xuất dữ liệu tài liệu trong thùng rác hoàn tất",
    )

@router.get("/{document_id}", response_model=APIResponse[DocumentResponse])
async def get_document_by_id(
    document_id: str,
    password: Optional[str] = Header(None, alias="x-document-password"),
    current_user: CurrentUser = Depends(get_current_user_optional),
) -> Any:
    return APIResponse(
        data=await DocumentService.get_document_by_id(
            document_id, current_user, password
        ),
        message="Trích xuất thông tin chi tiết tài liệu hoàn tất",
        status=status.HTTP_200_OK,
    )

@router.get("/tai-lieu/{slug}", response_model=APIResponse[DocumentResponse])
async def get_document_by_slug(
    slug: str, current_user: CurrentUser = Depends(get_current_user_optional)
) -> Any:
    return APIResponse(
        data=await DocumentService.get_document_by_slug(slug, current_user),
        message="Trích xuất tài liệu hoàn tất",
        status=status.HTTP_200_OK,
    )

@router.get("/{document_id}/khoa-giai-ma", response_model=APIResponse[Any])
async def get_document_decryption_key(
    document_id: str, current_user: CurrentUser = Depends(get_current_user_optional)
) -> Any:
    return APIResponse(
        data=await DocumentService.get_document_decryption_key(document_id, current_user),
        message="Trích xuất khóa giải mã tài liệu (decryption key) hoàn tất",
        status=status.HTTP_200_OK,
    )

@router.get("/xem-truoc/{slug}", response_model=APIResponse[Any])
async def get_document_preview(slug: str):
    return APIResponse(
        data=await DocumentService.get_document_preview(slug),
        message="Trích xuất bản xem trước tài liệu công khai hoàn tất",
    )

@router.delete(
    "/{document_id}",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def soft_delete_document(
    document_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    return APIResponse(
        data=await DocumentService.soft_delete_document(document_id, current_user),
        message="Tài liệu đã được di chuyển vào thùng rác hệ thống",
    )

@router.post(
    "/{document_id}/khoi-phuc",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def restore_document(
    document_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    return APIResponse(
        data=await DocumentService.restore_document(document_id, current_user),
        message="Tài liệu đã được khôi phục hoàn tất từ thùng rác",
    )

@router.post(
    "/{document_id}/bao-ve",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def set_document_password(
    document_id: str,
    req: DocumentPasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    return APIResponse(
        data=await DocumentService.set_document_password(
            document_id, req.password, current_user
        ),
        message="Thiết lập mật khẩu bảo vệ truy cập tài liệu hoàn tất",
    )

@router.get(
    "/{document_id}/nhat-ky-hoat-dong",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def get_document_audit_logs(
    document_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    return APIResponse(
        data=await DocumentService.get_document_audit_logs(document_id, current_user),
        message="Trích xuất nhật ký kiểm toán (audit log) của tài liệu hoàn tất",
    )

@router.post(
    "/{document_id}/danh-dau",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def toggle_star_document(
    document_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    res = await DocumentService.toggle_star_document(document_id, current_user)
    return APIResponse(
        data=res,
        message="Cập nhật trạng thái đánh dấu (star) ưu tiên của tài liệu hoàn tất",
    )

@router.post(
    "/{document_id}/chuyen-nhuong",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def transfer_document(
    document_id: str,
    new_owner_id: str = Query(...),
    current_user: CurrentUser = Depends(get_current_user),
):
    res = await DocumentService.transfer_document(document_id, new_owner_id, current_user)
    return APIResponse(
        data=res,
        message="Chuyển giao quyền sở hữu tài liệu cho người dùng mới hoàn tất",
    )

@router.get("/{document_id}/thong-ke", response_model=APIResponse[Any])
async def get_document_analytics(
    document_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    res = await DocumentService.get_document_analytics(document_id, current_user)
    return APIResponse(
        data=res,
        message="Trích xuất dữ liệu phân tích tương tác tài liệu (analytics) hoàn tất",
    )

@router.get("/{document_id}/chi-so-hoc-thuat", response_model=APIResponse[Any])
async def get_document_academic(
    document_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    res = await DocumentService.get_document_academic(document_id, current_user)
    return APIResponse(
        data=res,
        message="Trích xuất dữ liệu phân tích chỉ số học thuật của tài liệu hoàn tất",
    )

@router.put(
    "/{document_id}/the",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def update_tags(
    document_id: str,
    req: TagsUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    result = await DocumentService.update_document(
        document_id, DocumentUpdate(tags=req.tags), current_user
    )
    return APIResponse(data=result, message="Cập nhật danh sách thẻ (tags) phân loại tài liệu hoàn tất")

@router.put(
    "/{document_id}/len-lich",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def schedule_publish(
    document_id: str,
    req: ScheduleUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    result = await DocumentService.update_document(
        document_id,
        DocumentUpdate(publish_at=req.publish_at, scheduled_publish_at=req.publish_at),
        current_user,
    )
    return APIResponse(data=result, message="Thiết lập lịch trình xuất bản tự động cho tài liệu hoàn tất")

@router.post("/{document_id}/mo-khoa", response_model=APIResponse[Any])
async def unlock_document(
    document_id: str,
    password: str = Body(..., embed=True),
    current_user: CurrentUser = Depends(get_current_user_optional),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentService.get_document_by_id(
            document_id, current_user, password
        ),
        message="Xác thực quyền truy cập tài liệu hoàn tất",
        status=status.HTTP_200_OK,
    )
