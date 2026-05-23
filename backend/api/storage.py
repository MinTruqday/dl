from fastapi import APIRouter, Depends, HTTPException, Body, BackgroundTasks
from typing import List, Any, Optional
from core.response import APIResponse
from models.user import UserInDB, RoleEnum
from models.storage import StorageItemCreate, StorageItemUpdate, StorageItemResponse
from api.dependency import require_role
from services.storage import StorageService

router = APIRouter(prefix="/luu-tru")

@router.post("/thu-muc", response_model=APIResponse[StorageItemResponse])
async def create_folder(
    data: StorageItemCreate = Body(...),
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER]))
):
    data.is_folder = True
    item = await StorageService.create_item(data, current_user.id)
    return APIResponse(data=StorageItemResponse(**item.dict()), message="Tạo thư mục thành công", status=201)

@router.post("/tap-tin", response_model=APIResponse[StorageItemResponse])
async def create_file(
    background_tasks: BackgroundTasks,
    data: StorageItemCreate = Body(...),
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER]))
):
    from services.ai import AIService
    data.is_folder = False
    item = await StorageService.create_item(data, current_user.id)
    background_tasks.add_task(AIService.process_storage_file, str(item.id), current_user.id)
    return APIResponse(data=StorageItemResponse(**item.dict()), message="Tạo tập tin thành công", status=201)

@router.get("/danh-sach", response_model=APIResponse[List[StorageItemResponse]])
async def list_items(
    parent_id: Optional[str] = None,
    is_trashed: bool = False,
    is_starred: Optional[bool] = None,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER]))
):
    items = await StorageService.get_items_by_parent(parent_id, current_user.id, is_trashed, is_starred)
    response_items = [StorageItemResponse(**item.dict()) for item in items]
    return APIResponse(data=response_items, message="Lấy danh sách thành công", status=200)

@router.get("/tim-kiem", response_model=APIResponse[List[StorageItemResponse]])
async def search_items(q: str, type: Optional[str] = None, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER]))):
    items = await StorageService.search_items(q, current_user.id, type)
    return APIResponse(data=[StorageItemResponse(**item.dict()) for item in items], message="Tìm kiếm thành công", status=200)

@router.get("/gan-day", response_model=APIResponse[List[StorageItemResponse]])
async def get_recent_items(limit: int = 20, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER]))):
    items = await StorageService.get_recent_items(current_user.id, limit)
    return APIResponse(data=[StorageItemResponse(**item.dict()) for item in items], message="Lấy danh sách gần đây thành công", status=200)

@router.get("/quota", response_model=APIResponse[Any])
async def get_storage_quota(current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER]))):
    data = await StorageService.get_storage_quota(current_user.id)
    return APIResponse(data=data, message="Lấy hạn mức thành công", status=200)

@router.post("/tap-tin/{item_id}/shortcut", response_model=APIResponse[StorageItemResponse])
async def create_shortcut(
    item_id: str,
    target_parent_id: Optional[str] = Body(None, embed=True),
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER]))
):
    from fastapi import HTTPException
    item = await StorageService.create_shortcut(item_id, target_parent_id, current_user.id)
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp tin gốc")
    return APIResponse(data=StorageItemResponse(**item.dict()), message="Tạo lối tắt thành công", status=201)

@router.get("/tai-xuong-zip")
async def download_zip(
    ids: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER]))
):
    from fastapi import HTTPException
    from fastapi.responses import StreamingResponse
    import zipfile
    import io
    from core.storage import get_storage_client
    from core.config import settings

    item_ids = [i.strip() for i in ids.split(",") if i.strip()]
    if not item_ids:
        raise HTTPException(status_code=400, detail="Không có tệp tin nào được chọn")

    # In-memory zip
    zip_buffer = io.BytesIO()
    
    async with await get_storage_client() as storage_client:
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for i_id in item_ids:
                item = await StorageService.get_item(i_id, current_user.id)
                if item and not item.is_folder and item.url:
                    # Download from S3/MinIO
                    try:
                        resp = await storage_client.get_object(Bucket=settings.MINIO_BUCKET_NAME, Key=item.url)
                        file_data = await resp["Body"].read()
                        zip_file.writestr(item.name, file_data)
                    except Exception as e:
                        print(f"Error downloading {item.name}: {e}")
                        
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment; filename=storage_download.zip"}
    )

@router.put("/tap-tin/{item_id}", response_model=APIResponse[StorageItemResponse])
async def update_item(
    item_id: str,
    data: StorageItemUpdate = Body(...),
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER]))
):
    import uuid
    from uuid6 import uuid7
    if data.is_public and data.is_public is True:
        current_item = await StorageService.get_item(item_id, current_user.id)
        if current_item and not current_item.share_token:
            update_data_dict = data.dict(exclude_unset=True)
            update_data_dict["share_token"] = str(uuid7())
            item = await StorageService.update_item(item_id, current_user.id, StorageItemUpdate(**update_data_dict))
        else:
            item = await StorageService.update_item(item_id, current_user.id, data)
    else:
        item = await StorageService.update_item(item_id, current_user.id, data)
        
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy tập tin hoặc thư mục")
    return APIResponse(data=StorageItemResponse(**item.dict()), message="Cập nhật thành công", status=200)

@router.delete("/tap-tin/{item_id}", response_model=APIResponse[Any])
async def delete_item(
    item_id: str,
    hard_delete: bool = False,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER]))
):
    if hard_delete:
        success = await StorageService.delete_item(item_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Không tìm thấy tập tin hoặc thư mục")
        return APIResponse(data=None, message="Xóa vĩnh viễn thành công", status=200)
    else:
        item = await StorageService.update_item(item_id, current_user.id, StorageItemUpdate(is_trashed=True))
        if not item:
            raise HTTPException(status_code=404, detail="Không tìm thấy tập tin hoặc thư mục")
        return APIResponse(data=None, message="Đưa vào thùng rác thành công", status=200)

@router.post("/tap-tin/{item_id}/sao-chep", response_model=APIResponse[StorageItemResponse])
async def copy_item(
    item_id: str,
    target_parent_id: Optional[str] = Body(None, embed=True),
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER]))
):
    item = await StorageService.copy_item(item_id, current_user.id, target_parent_id)
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy tập tin hoặc thư mục")
    return APIResponse(data=StorageItemResponse(**item.dict()), message="Sao chép thành công", status=201)

@router.post("/tap-tin/{item_id}/version", response_model=APIResponse[StorageItemResponse])
async def add_version(
    item_id: str,
    url: str = Body(..., embed=True),
    size: int = Body(..., embed=True),
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER]))
):
    item = await StorageService.add_version(item_id, current_user.id, url, size)
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy tập tin")
    return APIResponse(data=StorageItemResponse(**item.dict()), message="Cập nhật phiên bản thành công", status=200)

@router.post("/tap-tin/{item_id}/chia-se", response_model=APIResponse[Any])
async def share_archive(
    item_id: str, 
    email: str = Body(..., embed=True),
    role: str = Body("viewer", embed=True),
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER]))
):
    from fastapi import HTTPException
    res = await StorageService.share_item(item_id, email, role, current_user.id)
    return APIResponse(data=None, message=res["message"], status=200)

@router.get("/chia-se/{share_token}", response_model=APIResponse[StorageItemResponse])
async def get_public_item(share_token: str):
    item = await StorageService.get_public_item(share_token)
    if not item:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Liên kết chia sẻ không hợp lệ hoặc đã bị vô hiệu hóa")
    return APIResponse(data=StorageItemResponse(**item.dict()), message="Lấy thông tin thành công", status=200)

