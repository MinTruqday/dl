from typing import Any
from fastapi import APIRouter, Depends, Query
from api.dependency import require_role
from models.user import UserInDB, RoleEnum
from core.response import APIResponse
from services.archive import ArchiveService
from models.archive import ArchiveUploadRequest, ArchiveRenameRequest, ArchiveDescriptionRequest, ArchiveShareRequest, ArchiveTagsRequest

router = APIRouter(prefix="/luu-tru")

@router.get("", response_model=APIResponse[Any])
async def get_my_archives(type: str = Query("all"), current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.MODERATOR]))):
    return APIResponse(
        data=await ArchiveService.get_archives(current_user, type),
        message="Lấy danh sách tệp tin thành công"
    )

@router.post("", response_model=APIResponse[Any])
async def upload_archive(data: ArchiveUploadRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    return APIResponse(
        data=await ArchiveService.upload_archive(data.model_dump(), current_user),
        message="Tải lên tệp tin thành công",
        status=201
    )

@router.delete("/{archive_id}", response_model=APIResponse[Any])
async def delete_archive(archive_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    return APIResponse(
        data=await ArchiveService.delete_archive(archive_id, current_user),
        message="Xóa tệp tin thành công"
    )

@router.patch("/{archive_id}/doi-ten", response_model=APIResponse[Any])
async def rename_archive(archive_id: str, data: ArchiveRenameRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    return APIResponse(
        data=await ArchiveService.rename_archive(archive_id, data.filename, current_user),
        message="Đổi tên tệp tin thành công"
    )

@router.patch("/{archive_id}/ghim", response_model=APIResponse[Any])
async def toggle_pin(archive_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    return APIResponse(
        data=await ArchiveService.toggle_pin_archive(archive_id, current_user),
        message="Cập nhật ghim tệp tin thành công"
    )

@router.patch("/{archive_id}/khoi-phuc", response_model=APIResponse[Any])
async def restore_archive(archive_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    return APIResponse(
        data=await ArchiveService.restore_archive(archive_id, current_user),
        message="Khôi phục tệp tin thành công"
    )

@router.delete("/{archive_id}/vinh-vien", response_model=APIResponse[Any])
async def permanently_delete_archive(archive_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    return APIResponse(
        data=await ArchiveService.permanently_delete_archive(archive_id, current_user),
        message="Xóa vĩnh viễn tệp tin thành công"
    )

@router.patch("/{archive_id}/mo-ta", response_model=APIResponse[Any])
async def update_description(archive_id: str, data: ArchiveDescriptionRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    return APIResponse(
        data=await ArchiveService.update_description(archive_id, data.description, current_user),
        message="Cập nhật mô tả tệp tin thành công"
    )

@router.patch("/{archive_id}/rieng-tu", response_model=APIResponse[Any])
async def toggle_visibility(archive_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    return APIResponse(
        data=await ArchiveService.toggle_visibility(archive_id, current_user),
        message="Cập nhật trạng thái hiển thị thành công"
    )

@router.post("/{archive_id}/chia-se", response_model=APIResponse[Any])
async def share_archive(archive_id: str, data: ArchiveShareRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    return APIResponse(
        data=await ArchiveService.share_archive(archive_id, data.email, current_user),
        message="Chia sẻ tệp tin thành công"
    )

@router.patch("/{archive_id}/nhan", response_model=APIResponse[Any])
async def update_tags(archive_id: str, data: ArchiveTagsRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    return APIResponse(
        data=await ArchiveService.update_tags(archive_id, data.tags, current_user),
        message="Cập nhật danh sách nhãn thành công"
    )
