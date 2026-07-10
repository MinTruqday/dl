import re
from typing import Any
from fastapi.responses import RedirectResponse

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from src.api.dependency import get_db, require_role
from src.services.upload import UploadService

from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role
from src.schemas.upload import PresignedUrlRequest, ConfirmUploadRequest

router = APIRouter(route_class=LoggingRoute, prefix="/tai-len")

async def validate_svg(file: UploadFile):
    if file.filename and file.filename.lower().endswith(".svg"):
        content = await file.read()
        text = content.decode("utf-8", errors="ignore")
        if re.search("<!ENTITY", text, re.IGNORECASE) or re.search(
            "<!DOCTYPE", text, re.IGNORECASE
        ):
            raise HTTPException(
                status_code=400, detail="Từ chối thao tác: Tệp đồ họa vector bị chặn do tiềm ẩn rủi ro bảo mật"
            )
        await file.seek(0)

@router.post("/hinh-anh", response_model=APIResponse[Any])
async def upload_image(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN])),
    db=Depends(get_db),
) -> Any:
    await validate_svg(file)
    return APIResponse(
        data=await UploadService.upload_image(file, owner_id=current_user.id, is_system=True),
        message="Truyền tải hình ảnh hoàn tất",
        status=201,
    )

@router.post("/tai-lieu", response_model=APIResponse[Any])
async def upload_document(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN])),
    db=Depends(get_db),
) -> Any:
    return APIResponse(
        data=await UploadService.upload_document(file, owner_id=current_user.id, is_system=True),
        message="Truyền tải và lưu trữ tài liệu hoàn tất",
        status=201,
    )

@router.post("/tap-tin", response_model=APIResponse[Any])
async def upload_asset(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(
        require_role([Role.READER, Role.AUTHOR, Role.ADMIN])
    ),
    db=Depends(get_db),
) -> Any:
    from src.services.storage import StorageService

    quota = await StorageService.get_storage_quota(current_user.id)
    if quota["used"] >= quota["limit"]:
        raise HTTPException(
            status_code=400,
            detail="Từ chối thao tác: Đã vượt quá giới hạn dung lượng lưu trữ cho phép",
        )
    return APIResponse(
        data=await UploadService.upload_document(file, owner_id=current_user.id, is_system=False),
        message="Truyền tải tệp tin hoàn tất",
        status=201,
    )

@router.post("/tin-nhan", response_model=APIResponse[Any])
async def upload_chat_attachment(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(
        require_role([Role.READER, Role.AUTHOR, Role.ADMIN])
    ),
    db=Depends(get_db),
) -> Any:
    from src.services.storage import StorageService
    from src.schemas.storage import StorageItemCreate
    from src.core.infrastructure.database import database
    from src.core.infrastructure.configuration import settings
    from datetime import datetime, timezone, timedelta

    user = await database.mongodb[settings.CLOUD_DB_NAME].users.find_one({"_id": current_user.id})
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin tài khoản người dùng tương ứng")
    
    ai_tier = user.get("ai_tier", "BASIC")
    is_admin = user.get("role") == "admin"

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if not is_admin and ai_tier != "BASIC":
        quota = await StorageService.get_storage_quota(current_user.id)
        if quota["used"] + file_size > quota["limit"]:
            raise HTTPException(
                status_code=400,
                detail="Dung lượng lưu trữ đã đầy, vui lòng nâng cấp gói cước hoặc xóa bớt dữ liệu"
            )

    result = await UploadService.upload_document(file, owner_id=current_user.id, is_system=False, is_message_attachment=True)
    file_url = result["url"]

    if ai_tier == "BASIC" and not is_admin:
        expires_at = datetime.now(timezone.utc) + timedelta(days=14)
        await database.mongodb[settings.CLOUD_DB_NAME].temp_chat_files.insert_one({
            "owner_id": current_user.id,
            "url": file_url,
            "original_filename": file.filename,
            "created_at": datetime.now(timezone.utc),
            "expires_at": expires_at
        })
        return APIResponse(
            data={"url": file_url, "filename": file.filename, "expires_in_days": 14},
            message="Truyền tải tệp đính kèm tạm thời hoàn tất",
            status=201
        )
    else:
        new_item = StorageItemCreate(
            name=file.filename,
            is_folder=False,
            url=file_url,
            size=file_size,
            mime_type=file.content_type,
            parent_id=None
        )
        await StorageService.create_item(new_item, current_user.id)
        
        return APIResponse(
            data={"url": file_url, "filename": file.filename},
            message="Truyền tải tệp đính kèm lưu trữ hoàn tất",
            status=201
        )

@router.post("/presigned-url", response_model=APIResponse[Any])
async def get_presigned_url_for_upload(
    req: PresignedUrlRequest,
    current_user: CurrentUser = Depends(
        require_role([Role.READER, Role.AUTHOR, Role.ADMIN])
    ),
    db=Depends(get_db),
) -> Any:
    from src.services.storage import StorageService
    from src.core.infrastructure.database import database
    from src.core.infrastructure.configuration import settings

    user = await database.mongodb[settings.CLOUD_DB_NAME].users.find_one({"_id": current_user.id})
    ai_tier = user.get("ai_tier", "BASIC") if user else "BASIC"
    is_admin = user.get("role") == "admin" if user else False

    if not req.is_system:
        if not (req.is_message_attachment and ai_tier == "BASIC"):
            quota = await StorageService.get_storage_quota(current_user.id)
            if quota["used"] + req.size > quota["limit"]:
                raise HTTPException(
                    status_code=400,
                    detail="Dung lượng lưu trữ đã đầy, vui lòng nâng cấp gói cước hoặc xóa bớt dữ liệu"
                )
            
    result = await UploadService.get_presigned_upload_url(
        filename=req.filename,
        content_type=req.content_type,
        owner_id=current_user.id,
        is_system=req.is_system,
        is_message_attachment=req.is_message_attachment
    )
    
    return APIResponse(
        data=result,
        message="Khởi tạo đường dẫn truyền tải bảo mật hoàn tất",
        status=200
    )

@router.post("/xac-nhan", response_model=APIResponse[Any])
async def confirm_upload(
    req: ConfirmUploadRequest,
    current_user: CurrentUser = Depends(
        require_role([Role.READER, Role.AUTHOR, Role.ADMIN])
    ),
    db=Depends(get_db),
) -> Any:
    from src.services.storage import StorageService
    from src.schemas.storage import StorageItemCreate
    from src.core.infrastructure.database import database
    from src.core.infrastructure.configuration import settings
    from datetime import datetime, timezone, timedelta
    
    user = await database.mongodb[settings.CLOUD_DB_NAME].users.find_one({"_id": current_user.id})
    ai_tier = user.get("ai_tier", "BASIC") if user else "BASIC"
    is_admin = user.get("role") == "admin" if user else False

    if req.is_message_attachment and ai_tier == "BASIC" and not is_admin:
        expires_at = datetime.now(timezone.utc) + timedelta(days=14)
        await database.mongodb[settings.CLOUD_DB_NAME].temp_chat_files.insert_one({
            "owner_id": current_user.id,
            "url": req.file_path,
            "original_filename": req.filename,
            "created_at": datetime.now(timezone.utc),
            "expires_at": expires_at
        })
        return APIResponse(
            data={"url": req.file_path, "filename": req.filename, "expires_in_days": 14},
            message="Xác thực truyền tải tệp đính kèm tạm thời hoàn tất",
            status=201
        )
    else:
        new_item = StorageItemCreate(
            name=req.filename,
            is_folder=False,
            url=req.file_path,
            size=req.size,
            mime_type=req.content_type,
            parent_id=None
        )
        await StorageService.create_item(new_item, current_user.id)
        
        try:
            from src.jobs.task import celery_app
            celery_app.send_task("src.tasks.compress_file_task", args=[req.file_path, req.content_type])
        except Exception as e:
            import logging
            logging.error(f"Failed to trigger compression task {e}")
                
        return APIResponse(
            data={"url": req.file_path, "filename": req.filename},
            message="Xác thực truyền tải tệp đính kèm lưu trữ hoàn tất",
            status=201
        )

@router.get("/luu-tru/{file_path:path}")
async def get_presigned_download_url(
    file_path: str,
    current_user: CurrentUser = Depends(
        require_role([Role.AUTHOR, Role.ADMIN, Role.READER])
    ),
    db=Depends(get_db),
):
    url_data = await UploadService.get_presigned_url(file_path)
    return RedirectResponse(url=url_data["download_url"], status_code=302)

@router.post("/phan-doan", response_model=APIResponse[Any])
async def upload_chunk(
    file: UploadFile = File(...),
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    filename: str = Form(...),
    current_user: CurrentUser = Depends(
        require_role([Role.READER, Role.AUTHOR, Role.ADMIN])
    ),
    db=Depends(get_db),
) -> Any:

    import os

    import aiofiles

    chunk_dir = f"storage/chunks/{upload_id}"
    os.makedirs(chunk_dir, exist_ok=True)
    chunk_path = os.path.join(chunk_dir, f"chunk_{chunk_index}")
    async with aiofiles.open(chunk_path, "wb") as f:
        while chunk := (await file.read(1024 * 1024)):
            await f.write(chunk)
    if len(os.listdir(chunk_dir)) == total_chunks:
        final_path = f"storage/tmp/{filename}"
        os.makedirs("storage/tmp", exist_ok=True)
        async with aiofiles.open(final_path, "wb") as outfile:
            for i in range(total_chunks):
                async with aiofiles.open(
                    os.path.join(chunk_dir, f"chunk_{i}"), "rb"
                ) as infile:
                    await outfile.write(await infile.read())

        class LocalFileWrapper:
            def __init__(self, p, n):
                self.file = open(p, "rb")
                self.filename = n

        local_file = LocalFileWrapper(final_path, filename)
        result = await UploadService.upload_document(local_file, owner_id=current_user.id, is_system=False)
        import shutil

        shutil.rmtree(chunk_dir)
        os.remove(final_path)
        return APIResponse(
            data=result, message="Truyền tải tệp tin hoàn tất", status=201
        )
    return APIResponse(
        data={"uploaded": chunk_index},
        message="Truyền tải phân đoạn dữ liệu tạm thời hoàn tất",
        status=200,
    )
