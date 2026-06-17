from core.config import settings
from typing import Any, List, Optional

from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query
from src.router.dependency_router import get_db, require_role
from src.schemas.storage_schema import (
    StorageItemCreate,
    StorageItemResponse,
    StorageItemUpdate,
)
from src.services.storage_service import StorageService
from loguru import logger

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
    item = await StorageService.create_item(data, current_user.id, db=db)
    return APIResponse(
        data=StorageItemResponse(**item.dict()),
        message="The new structural storage folder has been successfully created within your workspace",
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
    from src.services.ai import AIService

    data.is_folder = False
    item = await StorageService.create_item(data, current_user.id, db=db)
    background_tasks.add_task(
        AIService.process_storage_file, str(item.id), current_user.id
    )
    return APIResponse(
        data=StorageItemResponse(**item.dict()),
        message="The new file has been successfully uploaded and registered in your personal storage workspace",
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
    items = await StorageService.get_items_by_parent(
        parent_id, current_user.id, is_trashed, is_starred, db=db
    )
    response_items = [StorageItemResponse(**item.dict()) for item in items]
    return APIResponse(
        data=response_items, message="The requested directory contents have been successfully retrieved from your storage workspace", status=200
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
    items = await StorageService.search_items(q, current_user.id, type, db=db)
    return APIResponse(
        data=[StorageItemResponse(**item.dict()) for item in items],
        message="The search operation has been successfully completed and the matching files are returned",
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
    items = await StorageService.get_recent_items(current_user.id, limit, db=db)
    return APIResponse(
        data=[StorageItemResponse(**item.dict()) for item in items],
        message="The list of recently accessed storage items has been successfully compiled and retrieved",
        status=200,
    )


@router.get("/quota", response_model=APIResponse[Any])
async def get_storage_quota(
    current_user: UserInDB = Depends(
        require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER])
    ),
    db=Depends(get_db),
):
    data = await StorageService.get_storage_quota(current_user.id, db=db)
    return APIResponse(data=data, message="Your personal storage quota and utilization metrics have been successfully calculated", status=200)


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
    item = await StorageService.create_shortcut(
        item_id, target_parent_id, current_user.id, db=db
    )
    if not item:
        raise HTTPException(status_code=404, detail="The system was unable to locate the specified original file to create a shortcut")
    return APIResponse(
        data=StorageItemResponse(**item.dict()), message="A navigational shortcut to the specified file has been successfully created", status=201
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

    from core.config import settings
    from core.storage import get_storage_client
    from fastapi.responses import StreamingResponse

    item_ids = [i.strip() for i in ids.split(",") if i.strip()]
    if not item_ids:
        raise HTTPException(status_code=400, detail="The archive generation request was rejected because no files were specified for download")
    zip_buffer = io.BytesIO()
    async with await get_storage_client() as storage_client:
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for i_id in item_ids:
                item = await StorageService.get_item(i_id, current_user.id, db=db)
                if item and (not item.is_folder) and item.url:
                    try:
                        resp = await storage_client.get_object(
                            Bucket=settings.MINIO_BUCKET_NAME, Key=item.url
                        )
                        file_data = await resp["Body"].read()
                        zip_file.writestr(item.name, file_data)
                    except Exception:
                        logger.warning("The system encountered an unexpected disruption while attempting to retrieve a file for the archive package")
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
        current_item = await StorageService.get_item(item_id, current_user.id, db=db)
        if current_item and (not current_item.share_token):
            update_data_dict = data.dict(exclude_unset=True)
            update_data_dict["share_token"] = str(uuid7())
            item = await StorageService.update_item(
                item_id, current_user.id, StorageItemUpdate(**update_data_dict), db=db
            )
        else:
            item = await StorageService.update_item(
                item_id, current_user.id, data, db=db
            )
    else:
        item = await StorageService.update_item(item_id, current_user.id, data, db=db)
    if not item:
        raise HTTPException(
            status_code=404, detail="The system was unable to locate the specified file or folder within your storage workspace"
        )
    return APIResponse(
        data=StorageItemResponse(**item.dict()),
        message="The metadata associated with the specified storage item has been successfully updated",
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
        success = await StorageService.delete_item(item_id, current_user.id, db=db)
        if not success:
            raise HTTPException(
                status_code=404, detail="The system was unable to locate the specified file or folder within your storage workspace"
            )
        return APIResponse(data=None, message="The specified storage item has been permanently and irreversibly removed from the system", status=200)
    else:
        item = await StorageService.update_item(
            item_id, current_user.id, StorageItemUpdate(is_trashed=True), db=db
        )
        if not item:
            raise HTTPException(
                status_code=404, detail="The system was unable to locate the specified file or folder within your storage workspace"
            )
        return APIResponse(data=None, message="The specified storage item has been successfully moved to the temporary trash bin", status=200)


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
    item = await StorageService.copy_item(
        item_id, current_user.id, target_parent_id, db=db
    )
    if not item:
        raise HTTPException(
            status_code=404, detail="The system was unable to locate the specified file within your storage workspace"
        )
    return APIResponse(
        data=StorageItemResponse(**item.dict()), message="The specified storage item has been successfully duplicated to the requested destination", status=201
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
    item = await StorageService.add_version(item_id, current_user.id, url, size, db=db)
    if not item:
        raise HTTPException(status_code=404, detail="The system was unable to locate the specified file within your storage workspace")
    return APIResponse(
        data=StorageItemResponse(**item.dict()),
        message="The new version of the specified file has been successfully uploaded and recorded",
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
    res = await StorageService.share_item(item_id, email, role, current_user.id, db=db)
    return APIResponse(data=None, message=res["message"], status=200)


@router.get("/shares/{share_token}", response_model=APIResponse[StorageItemResponse])
async def get_public_item(share_token: str, db=Depends(get_db)):
    item = await StorageService.get_public_item(share_token, db=db)
    if not item:
        raise HTTPException(status_code=404, detail="The provided public sharing link is either structurally invalid or has expired")
    return APIResponse(
        data=StorageItemResponse(**item.dict()),
        message="The details of the publicly shared file have been successfully retrieved",
        status=200,
    )