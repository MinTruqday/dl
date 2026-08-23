from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from src.core.response import APIResponse
from src.api.dependency import get_db, require_role
from src.core.dependency import CurrentUser, Role
from src.schemas.storage import StorageItemCreate, StorageItemUpdate
from src.services.file import FileService

router = APIRouter(prefix="/tep-tin")


@router.post("", response_model=APIResponse[Any], status_code=201)
async def create_file_record(
    item: StorageItemCreate,
    current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])),
    db=Depends(get_db),
):
    result = await FileService.create_file_record(item, current_user.id)
    return APIResponse(
        data=result.model_dump(by_alias=True), message="Đăng ký tệp tin thành công", status=201
    )


@router.get("/dung-luong", response_model=APIResponse[Any])
async def get_storage_quota(
    current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])),
    db=Depends(get_db),
):
    quota = await FileService.get_storage_quota(current_user.id)
    return APIResponse(data=quota, message="Lấy thông tin dung lượng thành công")


@router.get("/{file_id}", response_model=APIResponse[Any])
async def get_file_metadata(
    file_id: str,
    current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])),
    db=Depends(get_db),
):
    result = await FileService.get_file_by_id(file_id, current_user.id)
    return APIResponse(
        data=result.model_dump(by_alias=True), message="Lấy thông tin tệp tin thành công"
    )


@router.patch("/{file_id}", response_model=APIResponse[Any])
async def update_file_metadata(
    file_id: str,
    update_data: StorageItemUpdate,
    current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])),
    db=Depends(get_db),
):
    result = await FileService.update_file_metadata(file_id, update_data, current_user.id)
    return APIResponse(data=result.model_dump(by_alias=True), message="Cập nhật tệp tin thành công")


@router.patch("/{file_id}/doi-ten", response_model=APIResponse[Any])
async def rename_file(
    file_id: str,
    req: dict,
    current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])),
    db=Depends(get_db),
):
    new_name = req.get("name")
    if not new_name:
        raise HTTPException(status_code=400, detail="Tên tệp tin mới không hợp lệ")
    res = await FileService.rename_file(file_id, new_name, current_user.id)
    return APIResponse(data=res, message="Đổi tên tệp tin thành công")


@router.patch("/{file_id}/di-chuyen", response_model=APIResponse[Any])
async def move_file(
    file_id: str,
    req: dict,
    current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])),
    db=Depends(get_db),
):
    new_parent_id = req.get("parent_id")
    res = await FileService.move_file(file_id, new_parent_id, current_user.id)
    return APIResponse(data=res, message="Di chuyển tệp tin thành công")
