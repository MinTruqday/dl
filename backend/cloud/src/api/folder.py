from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from src.core.response import APIResponse
from src.api.dependency import get_db, require_role
from src.core.dependency import CurrentUser, Role
from src.services.folder import FolderService

router = APIRouter(prefix="/thu-muc")

@router.post("", response_model=APIResponse[Any], status_code=201)
async def create_folder(
    req: dict,
    current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])),
    db=Depends(get_db),
):
    name = req.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Tên thư mục không được để trống")
    parent_id = req.get("parent_id")
    folder = await FolderService.create_folder(name, parent_id, current_user.id)
    return APIResponse(data=folder.model_dump(by_alias=True), message="Tạo thư mục thành công", status=201)

@router.get("/noi-dung", response_model=APIResponse[Any])
async def get_folder_contents(
    folder_id: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])),
    db=Depends(get_db),
):
    items = await FolderService.get_folder_contents(folder_id, current_user.id)
    return APIResponse(data=items, message="Lấy nội dung thư mục thành công")

@router.get("/cay-thu-muc", response_model=APIResponse[Any])
async def get_folder_tree(
    current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])),
    db=Depends(get_db),
):
    folders = await FolderService.get_folder_tree(current_user.id)
    return APIResponse(data=folders, message="Lấy cây thư mục thành công")

@router.patch("/{folder_id}/doi-ten", response_model=APIResponse[Any])
async def rename_folder(
    folder_id: str,
    req: dict,
    current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])),
    db=Depends(get_db),
):
    new_name = req.get("name")
    if not new_name:
        raise HTTPException(status_code=400, detail="Tên thư mục mới không hợp lệ")
    res = await FolderService.rename_folder(folder_id, new_name, current_user.id)
    return APIResponse(data=res, message="Đổi tên thư mục thành công")

@router.patch("/{folder_id}/di-chuyen", response_model=APIResponse[Any])
async def move_folder(
    folder_id: str,
    req: dict,
    current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])),
    db=Depends(get_db),
):
    new_parent_id = req.get("parent_id")
    res = await FolderService.move_folder(folder_id, new_parent_id, current_user.id)
    return APIResponse(data=res, message="Di chuyển thư mục thành công")
