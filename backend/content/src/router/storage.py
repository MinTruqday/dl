from typing import Any, List, Optional

from fastapi import (APIRouter, BackgroundTasks, Body, Depends, HTTPException,
                     Query)
from loguru import logger
from src.router.dependency import get_db, require_role
from src.schemas.storage import (StorageItemCreate, StorageItemResponse,
                                 StorageItemUpdate)
from src.services.storage import StorageManager

from core.config import settings
from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB

router = APIRouter(prefix="/storage")


@router.post("/folders", response_model=APIResponse[StorageItemResponse])
async def create_folder(
    data: StorageItemCreate = Body(...),
    current_user: UserInDB = Depends(
        require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER])
    ),
    db=Depends(get_db),
):
    data.is_folder = True
    item = await StorageManager.create_item(data, current_user.id, db=db)
    return APIResponse(
        data=StorageItemResponse(**item.dict()),
        message="Tạo thư mục mới thành công",
        status=201,
    )


@router.post("/files", response_model=APIResponse[StorageItemResponse])
async def create_file(
    background_tasks: BackgroundTasks,
    data: StorageItemCreate = Body(...),
    current_user: UserInDB = Depends(
        require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER])
    ),
    db=Depends(get_db),
):
    # FIXME: Missing module: from src.services.ai import AIManager

    data.is_folder = False
    item = await StorageManager.create_item(data, current_user.id, db=db)
    background_tasks.add_task(
        # AIManager.process_storage_file, str(item.id), current_user.id
    )
    return APIResponse(
        data=StorageItemResponse(**item.dict()),
        message="Tải lên tệp tin cá nhân thành công",
        status=201,
    )


@router.get("/lists", response_model=APIResponse[List[StorageItemResponse]])
async def list_items(
    parent_id: Optional[str] = None,
    is_trashed: bool = False,
    is_starred: Optional[bool] = None,
    current_user: UserInDB = Depends(
        require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER])
    ),
    db=Depends(get_db),
):
    items = await StorageManager.get_items_by_parent(
        parent_id, current_user.id, is_trashed, is_starred, db=db
    )
    response_items = [StorageItemResponse(**item.dict()) for item in items]
    return APIResponse(
        data=response_items, message="Lấy nội dung thư mục thành công", status=200
    )


@router.get("/search", response_model=APIResponse[List[StorageItemResponse]])
async def search_items(
    q: str,
    type: Optional[str] = None,
    current_user: UserInDB = Depends(
        require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER])
    ),
    db=Depends(get_db),
):
    items = await StorageManager.search_items(q, current_user.id, type, db=db)
    return APIResponse(
        data=[StorageItemResponse(**item.dict()) for item in items],
        message="Tìm kiếm thành công",
        status=200,
    )


@router.get("/recent", response_model=APIResponse[List[StorageItemResponse]])
async def get_recent_items(
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    current_user: UserInDB = Depends(
        require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER])
    ),
    db=Depends(get_db),
):
    items = await StorageManager.get_recent_items(current_user.id, limit, db=db)
    return APIResponse(
        data=[StorageItemResponse(**item.dict()) for item in items],
        message="Lấy danh sách tệp truy cập gần đây thành công",
        status=200,
    )


@router.get("/quota", response_model=APIResponse[Any])
async def get_storage_quota(
    current_user: UserInDB = Depends(
        require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER])
    ),
    db=Depends(get_db),
):
    data = await StorageManager.get_storage_quota(current_user.id, db=db)
    return APIResponse(
        data=data, message="Cập nhật dung lượng lưu trữ thành công", status=200
    )


@router.post(
    "/tap-tin/{item_id}/loi-tat", response_model=APIResponse[StorageItemResponse]
)
async def create_shortcut(
    item_id: str,
    target_parent_id: Optional[str] = Body(None, embed=True),
    current_user: UserInDB = Depends(
        require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER])
    ),
    db=Depends(get_db),
):
    item = await StorageManager.create_shortcut(
        item_id, target_parent_id, current_user.id, db=db
    )
    if not item:
        raise HTTPException(
            status_code=404, detail="Không tìm thấy tệp gốc để tạo lối tắt"
        )
    return APIResponse(
        data=StorageItemResponse(**item.dict()),
        message="Tạo lối tắt tệp thành công",
        status=201,
    )


@router.get("/download-archive")
async def download_zip(
    ids: str,
    current_user: UserInDB = Depends(
        require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER])
    ),
    db=Depends(get_db),
):
    import io
    import zipfile

    from fastapi.responses import StreamingResponse

    from core.config import settings
    from core.storage import get_storage_client

    item_ids = [i.strip() for i in ids.split(",") if i.strip()]
    if not item_ids:
        raise HTTPException(
            status_code=400, detail="Lỗi tạo tệp nén do không có tệp nào được chọn"
        )
    zip_buffer = io.BytesIO()
    async with await get_storage_client() as storage_client:
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for i_id in item_ids:
                item = await StorageManager.get_item(i_id, current_user.id, db=db)
                if item and (not item.is_folder) and item.url:
                    try:
                        resp = await storage_client.get_object(
                            Bucket=settings.MINIO_BUCKET_NAME, Key=item.url
                        )
                        file_data = await resp["Body"].read()
                        zip_file.writestr(item.name, file_data)
                    except Exception:
                        logger.warning("Lỗi tải tệp nén")
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": "attachment; filename=storage_download.zip"},
    )


@router.put("/files/{item_id}", response_model=APIResponse[StorageItemResponse])
async def update_item(
    item_id: str,
    data: StorageItemUpdate = Body(...),
    current_user: UserInDB = Depends(
        require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER])
    ),
    db=Depends(get_db),
):
    from uuid6 import uuid7

    if data.is_public and data.is_public is True:
        current_item = await StorageManager.get_item(item_id, current_user.id, db=db)
        if current_item and (not current_item.share_token):
            update_data_dict = data.dict(exclude_unset=True)
            update_data_dict["share_token"] = str(uuid7())
            item = await StorageManager.update_item(
                item_id, current_user.id, StorageItemUpdate(**update_data_dict), db=db
            )
        else:
            item = await StorageManager.update_item(
                item_id, current_user.id, data, db=db
            )
    else:
        item = await StorageManager.update_item(item_id, current_user.id, data, db=db)
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp hoặc thư mục")
    return APIResponse(
        data=StorageItemResponse(**item.dict()),
        message="Cập nhật dữ liệu tệp lưu trữ thành công",
        status=200,
    )


@router.delete("/files/{item_id}", response_model=APIResponse[Any])
async def delete_item(
    item_id: str,
    hard_delete: bool = False,
    current_user: UserInDB = Depends(
        require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER])
    ),
    db=Depends(get_db),
):
    if hard_delete:
        success = await StorageManager.delete_item(item_id, current_user.id, db=db)
        if not success:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy tệp hoặc thư mục"
            )
        return APIResponse(
            data=None, message="Đã xóa vĩnh viễn dữ liệu lưu trữ", status=200
        )
    else:
        item = await StorageManager.update_item(
            item_id, current_user.id, StorageItemUpdate(is_trashed=True), db=db
        )
        if not item:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy tệp hoặc thư mục"
            )
        return APIResponse(data=None, message="Đã chuyển mục vào thùng rác", status=200)


@router.post(
    "/tap-tin/{item_id}/sao-chep", response_model=APIResponse[StorageItemResponse]
)
async def copy_item(
    item_id: str,
    target_parent_id: Optional[str] = Body(None, embed=True),
    current_user: UserInDB = Depends(
        require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER])
    ),
    db=Depends(get_db),
):
    item = await StorageManager.copy_item(
        item_id, current_user.id, target_parent_id, db=db
    )
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp tin")
    return APIResponse(
        data=StorageItemResponse(**item.dict()),
        message="Sao chép tệp thành công",
        status=201,
    )


@router.post(
    "/tap-tin/{item_id}/phien-ban", response_model=APIResponse[StorageItemResponse]
)
async def add_version(
    item_id: str,
    url: str = Body(..., embed=True),
    size: int = Body(..., embed=True),
    current_user: UserInDB = Depends(
        require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER])
    ),
    db=Depends(get_db),
):
    item = await StorageManager.add_version(item_id, current_user.id, url, size, db=db)
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp tin")
    return APIResponse(
        data=StorageItemResponse(**item.dict()),
        message="Cập nhật phiên bản mới thành công",
        status=200,
    )


@router.post("/files/{item_id}/share", response_model=APIResponse[Any])
async def share_archive(
    item_id: str,
    email: str = Body(..., embed=True),
    role: str = Body("viewer", embed=True),
    current_user: UserInDB = Depends(
        require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER])
    ),
    db=Depends(get_db),
):
    res = await StorageManager.share_item(item_id, email, role, current_user.id, db=db)
    return APIResponse(data=None, message=res["message"], status=200)


@router.get("/shares/{share_token}", response_model=APIResponse[StorageItemResponse])
async def get_public_item(share_token: str, db=Depends(get_db)):
    item = await StorageManager.get_public_item(share_token, db=db)
    if not item:
        raise HTTPException(
            status_code=404, detail="Liên kết chia sẻ không hợp lệ hoặc đã hết hạn"
        )
    return APIResponse(
        data=StorageItemResponse(**item.dict()),
        message="Lấy thông tin tệp chia sẻ thành công",
        status=200,
    )
