import io
import zipfile
from core.config import settings
from typing import Any, List, Optional
from core.response import APIResponse
from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query
from core.dependency import get_db, require_role
from src.schemas.storage import StorageItemCreate, StorageItemResponse, StorageItemUpdate
from src.services.storage import StorageService
from loguru import logger
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/luu-tru")

@router.post("/thu-muc", response_model=APIResponse[StorageItemResponse])
async def create_folder(data: StorageItemCreate = Body(...), current_user: dict = Depends(require_role(["author", "admin", "reader"])), db=Depends(get_db)):
    data.is_folder = True
    item = await StorageService.create_item(data, current_user.get("id"), db=db)
    return APIResponse(
        data=StorageItemResponse(**item.dict()),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=201,
    )

@router.post("/tap-tin", response_model=APIResponse[StorageItemResponse])
async def create_file(background_tasks: BackgroundTasks, data: StorageItemCreate = Body(...), current_user: dict = Depends(require_role(["author", "admin", "reader"])), db=Depends(get_db)):
    from src.services.ai import AIService
    data.is_folder = False
    item = await StorageService.create_item(data, current_user.get("id"), db=db)
    background_tasks.add_task(AIService.process_storage_file, str(item.id), current_user.get("id"))
    return APIResponse(
        data=StorageItemResponse(**item.dict()),
        message="Lỗi truy xuất cơ sở dữ liệu hệ thống",
        status=201,
    )

@router.get("/danh-sach", response_model=APIResponse[List[StorageItemResponse]])
async def list_items(parent_id: Optional[str] = None, is_trashed: bool = False, is_starred: Optional[bool] = None, current_user: dict = Depends(require_role(["author", "admin", "reader"])), db=Depends(get_db)):
    items = await StorageService.get_items_by_parent(parent_id, current_user.get("id"), is_trashed, is_starred, db=db)
    return APIResponse(
        data=[StorageItemResponse(**item.dict()) for item in items], 
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công", 
        status=200
    )

@router.get("/tim-kiem", response_model=APIResponse[List[StorageItemResponse]])
async def search_items(q: str, type: Optional[str] = None, current_user: dict = Depends(require_role(["author", "admin", "reader"])), db=Depends(get_db)):
    items = await StorageService.search_items(q, current_user.get("id"), type, db=db)
    return APIResponse(
        data=[StorageItemResponse(**item.dict()) for item in items],
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )

@router.get("/gan-day", response_model=APIResponse[List[StorageItemResponse]])
async def get_recent_items(limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), current_user: dict = Depends(require_role(["author", "admin", "reader"])), db=Depends(get_db)):
    items = await StorageService.get_recent_items(current_user.get("id"), limit, db=db)
    return APIResponse(
        data=[StorageItemResponse(**item.dict()) for item in items],
        message="Lỗi truy xuất cơ sở dữ liệu hệ thống",
        status=200,
    )

@router.get("/han-muc", response_model=APIResponse[Any])
async def get_storage_quota(current_user: dict = Depends(require_role(["author", "admin", "reader"])), db=Depends(get_db)):
    data = await StorageService.get_storage_quota(current_user.get("id"), db=db)
    return APIResponse(data=data, message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công", status=200)

@router.post("/tap-tin/{item_id}/loi-tat", response_model=APIResponse[StorageItemResponse])
async def create_shortcut(item_id: str, target_parent_id: Optional[str] = Body(None, embed=True), current_user: dict = Depends(require_role(["author", "admin", "reader"])), db=Depends(get_db)):
    item = await StorageService.create_shortcut(item_id, target_parent_id, current_user.get("id"), db=db)
    if not item:
        raise HTTPException(status_code=404, detail="Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
    return APIResponse(
        data=StorageItemResponse(**item.dict()), 
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công", 
        status=201
    )

@router.get("/tai-xuong-luu-tru-cu")
async def download_zip(ids: str, current_user: dict = Depends(require_role(["author", "admin", "reader"])), db=Depends(get_db)):
    from core.storage import get_storage_client
    item_ids = [i.strip() for i in ids.split(",") if i.strip()]
    if not item_ids:
        raise HTTPException(status_code=400, detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
    
    zip_buffer = io.BytesIO()
    async with await get_storage_client() as storage_client:
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for i_id in item_ids:
                item = await StorageService.get_item(i_id, current_user.get("id"), db=db)
                if item and (not item.is_folder) and item.url:
                    try:
                        resp = await storage_client.get_object(Bucket=settings.MINIO_BUCKET_NAME, Key=item.url)
                        file_data = await resp["Body"].read()
                        zip_file.writestr(item.name, file_data)
                    except Exception:
                        logger.warning("Mất kết nối mạng tạm thời")
    zip_buffer.seek(0)
    return StreamingResponse(zip_buffer, media_type="application/x-zip-compressed", headers={"Content-Disposition": "attachment; filename=storage_download.zip"})

@router.put("/tap-tin/{item_id}", response_model=APIResponse[StorageItemResponse])
async def update_item(item_id: str, data: StorageItemUpdate = Body(...), current_user: dict = Depends(require_role(["author", "admin", "reader"])), db=Depends(get_db)):
    from uuid6 import uuid7
    if data.is_public and data.is_public is True:
        current_item = await StorageService.get_item(item_id, current_user.get("id"), db=db)
        if current_item and (not current_item.share_token):
            update_data_dict = data.dict(exclude_unset=True)
            update_data_dict["share_token"] = str(uuid7())
            item = await StorageService.update_item(item_id, current_user.get("id"), StorageItemUpdate(**update_data_dict), db=db)
        else:
            item = await StorageService.update_item(item_id, current_user.get("id"), data, db=db)
    else:
        item = await StorageService.update_item(item_id, current_user.get("id"), data, db=db)
        
    if not item:
        raise HTTPException(status_code=404, detail="Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
    return APIResponse(
        data=StorageItemResponse(**item.dict()),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )

@router.delete("/tap-tin/{item_id}", response_model=APIResponse[Any])
async def delete_item(item_id: str, hard_delete: bool = False, current_user: dict = Depends(require_role(["author", "admin", "reader"])), db=Depends(get_db)):
    if hard_delete:
        success = await StorageService.delete_item(item_id, current_user.get("id"), db=db)
        if not success:
            raise HTTPException(status_code=404, detail="Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
        return APIResponse(data=None, message="Lỗi truy xuất cơ sở dữ liệu hệ thống", status=200)
    
    item = await StorageService.update_item(item_id, current_user.get("id"), StorageItemUpdate(is_trashed=True), db=db)
    if not item:
        raise HTTPException(status_code=404, detail="Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
    return APIResponse(data=None, message="Lỗi truy xuất cơ sở dữ liệu hệ thống", status=200)

@router.post("/tap-tin/{item_id}/sao-chep", response_model=APIResponse[StorageItemResponse])
async def copy_item(item_id: str, target_parent_id: Optional[str] = Body(None, embed=True), current_user: dict = Depends(require_role(["author", "admin", "reader"])), db=Depends(get_db)):
    item = await StorageService.copy_item(item_id, current_user.get("id"), target_parent_id, db=db)
    if not item:
        raise HTTPException(status_code=404, detail="Lỗi khi truy xuất tài liệu")
    return APIResponse(
        data=StorageItemResponse(**item.dict()), 
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn", 
        status=201
    )

@router.post("/tap-tin/{item_id}/phien-lam-cam-quyen", response_model=APIResponse[StorageItemResponse])
async def add_version(item_id: str, url: str = Body(..., embed=True), size: int = Body(..., embed=True), current_user: dict = Depends(require_role(["author", "admin", "reader"])), db=Depends(get_db)):
    item = await StorageService.add_version(item_id, current_user.get("id"), url, size, db=db)
    if not item:
        raise HTTPException(status_code=404, detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
    return APIResponse(
        data=StorageItemResponse(**item.dict()),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
        status=200,
    )

@router.post("/tap-tin/{item_id}/chia-se", response_model=APIResponse[Any])
async def share_archive(item_id: str, email: str = Body(..., embed=True), role: str = Body("viewer", embed=True), current_user: dict = Depends(require_role(["author", "admin", "reader"])), db=Depends(get_db)):
    res = await StorageService.share_item(item_id, email, role, current_user.get("id"), db=db)
    return APIResponse(data=None, message=res["message"], status=200)

@router.get("/chia-se/{share_token}", response_model=APIResponse[StorageItemResponse])
async def get_public_item(share_token: str, db=Depends(get_db)):
    item = await StorageService.get_public_item(share_token, db=db)
    if not item:
        raise HTTPException(status_code=404, detail="Từ chối truy cập API nội bộ")
    return APIResponse(
        data=StorageItemResponse(**item.dict()),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )