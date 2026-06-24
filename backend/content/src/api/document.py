from datetime import datetime, timezone
from typing import Any, List, Optional

from bson import ObjectId
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
    DRMSettingsUpdate,
    TagsUpdate,
    ScheduleUpdate,
)
from src.services.document import DocumentService

from shared.infrastructure.configuration import settings
from shared.infrastructure.database import database
from shared.response import APIResponse
from shared.dependency import CurrentUser, Role

router = APIRouter(prefix="/tai-lieu")


@router.post("", response_model=APIResponse[DocumentResponse])
async def create_document(
    doc_in: DocumentCreate,
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN])),
) -> Any:
    return APIResponse(
        data=await DocumentService.create_document(doc_in, current_user),
        message="Tạo tài liệu mới thành công",
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
        message="Lưu thay đổi nội dung tài liệu thành công",
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
        message="Cập nhật dữ liệu mô tả tài liệu thành công",
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
        message="Lấy danh mục tài liệu thành công",
        status=status.HTTP_200_OK,
    )



@router.get(
    "/thu-muc",
    response_model=APIResponse[Any],
    dependency=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def get_folders(
    parent_id: Optional[str] = None, current_user: CurrentUser = Depends(get_current_user)
):
    folders = await DocumentService.get_folders(parent_id, current_user)
    return APIResponse(data=folders, message="Lấy cấu trúc thư mục thành công")


@router.post(
    "/thu-muc",
    response_model=APIResponse[Any],
    dependency=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def create_folder(
    req: FolderCreate, current_user: CurrentUser = Depends(get_current_user)
):
    folder_doc = await DocumentService.create_folder(req.name, req.parent_id, current_user)
    return APIResponse(data=folder_doc, message="Tạo thư mục làm việc thành công")


@router.delete(
    "/thu-muc/{folder_id}",
    response_model=APIResponse[Any],
    dependency=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def delete_folder(
    folder_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    res = await DocumentService.delete_folder(folder_id, current_user)
    return APIResponse(
        data=res, message="Xóa thư mục vĩnh viễn thành công"
    )


@router.get(
    "/ca-nhan",
    response_model=APIResponse[Any],
    dependency=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
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
        message="Lấy danh sách tài liệu cá nhân thành công",
    )


@router.get(
    "/thung-rac",
    response_model=APIResponse[Any],
    dependency=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def get_trash(current_user: CurrentUser = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.get_trash(current_user),
        message="Lấy nội dung thùng rác thành công",
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
        message="Lấy thông tin chi tiết tài liệu thành công",
        status=status.HTTP_200_OK,
    )


@router.get("/tai-lieu/{slug}", response_model=APIResponse[DocumentResponse])
async def get_document_by_slug(
    slug: str, current_user: CurrentUser = Depends(get_current_user_optional)
) -> Any:
    return APIResponse(
        data=await DocumentService.get_document_by_slug(slug, current_user),
        message="Lấy tài liệu thành công",
        status=status.HTTP_200_OK,
    )

@router.get("/{document_id}/khoa-giai-ma", response_model=APIResponse[Any])
async def get_document_decryption_key(
    document_id: str, current_user: CurrentUser = Depends(get_current_user_optional)
) -> Any:
    return APIResponse(
        data=await DocumentService.get_document_decryption_key(document_id, current_user),
        message="Lấy khoá giải mã thành công",
        status=status.HTTP_200_OK,
    )


@router.get("/xem-truoc/{slug}", response_model=APIResponse[Any])
async def get_document_preview(slug: str):
    return APIResponse(
        data=await DocumentService.get_document_preview(slug),
        message="Lấy bản xem trước tài liệu công khai thành công",
    )


@router.delete(
    "/{document_id}",
    response_model=APIResponse[Any],
    dependency=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def soft_delete_document(
    document_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    return APIResponse(
        data=await DocumentService.soft_delete_document(document_id, current_user),
        message="Đã chuyển tài liệu vào thùng rác",
    )


@router.post(
    "/{document_id}/khoi-phuc",
    response_model=APIResponse[Any],
    dependency=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def restore_document(
    document_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    return APIResponse(
        data=await DocumentService.restore_document(document_id, current_user),
        message="Tài liệu của bạn đã được khôi phục thành công về trạng thái ban đầu",
    )


@router.post(
    "/{document_id}/bao-ve",
    response_model=APIResponse[Any],
    dependency=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
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
        message="Thiết lập mật khẩu truy cập tài liệu thành công",
    )


@router.get(
    "/{document_id}/nhat-ky-hoat-dong",
    response_model=APIResponse[Any],
    dependency=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def get_document_audit_logs(
    document_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    return APIResponse(
        data=await DocumentService.get_document_audit_logs(document_id, current_user),
        message="Lấy nhật ký hoạt động tài liệu thành công",
    )


@router.post(
    "/{document_id}/danh-dau",
    response_model=APIResponse[Any],
    dependency=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def toggle_star_document(
    document_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    res = await DocumentService.toggle_star_document(document_id, current_user)
    return APIResponse(
        data=res,
        message="Cập nhật trạng thái ưu tiên tài liệu thành công",
    )


@router.post(
    "/{document_id}/chuyen-nhuong",
    response_model=APIResponse[Any],
    dependency=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def transfer_document(
    document_id: str,
    new_owner_id: str = Query(...),
    current_user: CurrentUser = Depends(get_current_user),
):
    res = await DocumentService.transfer_document(document_id, new_owner_id, current_user)
    return APIResponse(
        data=res,
        message="Đã chuyển quyền sở hữu tài liệu",
    )


@router.get("/{document_id}/thong-ke", response_model=APIResponse[Any])
async def get_document_analytics(
    document_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    res = await DocumentService.get_document_analytics(document_id, current_user)
    return APIResponse(
        data=res,
        message="Lấy dữ liệu tương tác người đọc thành công",
    )


@router.get("/{document_id}/chi-so-hoc-thuat", response_model=APIResponse[Any])
async def get_document_academic(
    document_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    res = await DocumentService.get_document_academic(document_id, current_user)
    return APIResponse(
        data=res,
        message="Lấy dữ liệu phân tích tài liệu thành công",
    )



@router.put(
    "/{document_id}/ban-quyen",
    response_model=APIResponse[Any],
    dependency=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def update_drm_settings(
    document_id: str,
    req: DRMSettingsUpdate,
    current_user: CurrentUser = Depends(get_current_user),
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
    return APIResponse(
        data=result, message="Cập nhật cấu hình bảo vệ bản quyền thành công"
    )



@router.put(
    "/{document_id}/the",
    response_model=APIResponse[Any],
    dependency=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def update_tags(
    document_id: str,
    req: TagsUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    result = await DocumentService.update_document(
        document_id, DocumentUpdate(tags=req.tags), current_user
    )
    return APIResponse(data=result, message="Cập nhật thẻ danh mục tài liệu thành công")



@router.put(
    "/{document_id}/len-lich",
    response_model=APIResponse[Any],
    dependency=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
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
    return APIResponse(data=result, message="Lên lịch xuất bản tài liệu thành công")


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
        message="Xác thực truy cập thành công",
        status=status.HTTP_200_OK,
    )
