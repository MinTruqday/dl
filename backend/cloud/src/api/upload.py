import json
import os
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

import aiofiles
import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import RedirectResponse, Response

from src.api.dependency import get_db, require_role
from src.core.dependency import CurrentUser, Role, Tier
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.infrastructure.redis import redis
from src.core.logging_route import LoggingRoute
from src.core.response import APIResponse
from src.core.storage import download_file, get_bucket, get_storage_client
from src.schemas.storage import StorageItemCreate
from src.schemas.upload import ConfirmUploadRequest, PresignedUrlRequest
from src.services.storage import StorageService
from src.services.upload import UploadService

router = APIRouter(route_class=LoggingRoute, prefix="/tai-len")


async def validate_svg(file: UploadFile):
    if file.filename and file.filename.lower().endswith(".svg"):
        content = await file.read(settings.MAX_UPLOAD_SIZE_BYTES + 1)
        text = content.decode("utf-8", errors="ignore")
        if re.search("<!ENTITY", text, re.IGNORECASE) or re.search("<!DOCTYPE", text, re.IGNORECASE):
            raise HTTPException(status_code=400, detail="Tệp đồ họa vector không an toàn")
        await file.seek(0)


async def file_size(file: UploadFile) -> int:
    await file.seek(0)
    file.file.seek(0, 2)
    size = file.file.tell()
    await file.seek(0)
    if size < settings.MIN_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="Tệp tải lên không được để trống")
    if size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Tệp tải lên vượt quá kích thước cho phép")
    return size


async def enforce_quota(user_id: str, additional_size: int):
    quota = await StorageService.get_storage_quota(user_id)
    if quota["used"] + additional_size > quota["limit"]:
        raise HTTPException(status_code=400, detail="Dung lượng lưu trữ đã đầy")


async def register_item(result: dict, user_id: str):
    return await StorageService.create_item(
        StorageItemCreate(
            name=result["filename"],
            is_folder=False,
            url=result["url"],
            size=result["size"],
            mime_type=result["content_type"],
        ),
        user_id,
    )


async def can_download(file_path: str, user_id: str, role: Role) -> bool:
    if ".." in file_path or file_path.startswith("/"):
        return False
    if file_path.startswith("public/"):
        return True
    if file_path.startswith((f"users/{user_id}/", f"client/{user_id}/")):
        return True
    if file_path.startswith(f"temp/{user_id}/"):
        return True
    db = database.mongodb[settings.CLOUD_DB_NAME]
    query = {
        "url": file_path,
        "is_trashed": False,
        "$or": [{"owner_id": user_id}, {"shared_with.user_id": user_id}],
    }
    if await db.storage_items.find_one(query, {"_id": 1}):
        return True
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{settings.MESSAGING_URL}/tin-nhan/noi-bo/quyen-truy-cap-tep",
                json={"file_path": file_path, "user_id": user_id},
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
        if response.status_code == 200 and response.json().get("allowed") is True:
            return True
    except (httpx.HTTPError, ValueError):
        pass
    return role == Role.ADMIN and file_path.startswith("system/")


@router.post("/hinh-anh", response_model=APIResponse[Any], status_code=201)
async def upload_image(file: UploadFile = File(...), current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN])), db=Depends(get_db)) -> Any:
    await validate_svg(file)
    result = await UploadService.upload_image(file, owner_id=current_user.id, is_system=True)
    return APIResponse(data=result, message="Truyền tải hình ảnh hoàn tất", status=201)


@router.post("/tai-lieu", response_model=APIResponse[Any], status_code=201)
async def upload_document(file: UploadFile = File(...), current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN])), db=Depends(get_db)) -> Any:
    result = await UploadService.upload_document(file, owner_id=current_user.id, is_system=True)
    return APIResponse(data=result, message="Truyền tải và lưu trữ tài liệu hoàn tất", status=201)


@router.post("/tap-tin", response_model=APIResponse[Any], status_code=201)
async def upload_asset(file: UploadFile = File(...), current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])), db=Depends(get_db)) -> Any:
    size = await file_size(file)
    await enforce_quota(current_user.id, size)
    result = await UploadService.upload_document(file, owner_id=current_user.id)
    item = await register_item(result, current_user.id)
    return APIResponse(data={**result, "item_id": item.id}, message="Truyền tải tệp tin hoàn tất", status=201)


@router.post("/tin-nhan", response_model=APIResponse[Any], status_code=201)
async def upload_chat_attachment(file: UploadFile = File(...), current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])), db=Depends(get_db)) -> Any:
    size = await file_size(file)
    is_temporary = current_user.ai_tier.upper() == Tier.BASIC.value and current_user.role != Role.ADMIN
    if not is_temporary:
        await enforce_quota(current_user.id, size)
    result = await UploadService.upload_document(file, owner_id=current_user.id, is_message_attachment=True, is_temporary=is_temporary)
    if is_temporary:
        expires_at = datetime.now(timezone.utc) + timedelta(days=14)
        await database.mongodb[settings.CLOUD_DB_NAME].temp_chat_files.insert_one({
            "owner_id": current_user.id,
            "url": result["url"],
            "original_filename": result["filename"],
            "created_at": datetime.now(timezone.utc),
            "expires_at": expires_at,
        })
        result["expires_in_days"] = 14
    else:
        item = await register_item(result, current_user.id)
        result["item_id"] = item.id
    return APIResponse(data=result, message="Truyền tải tệp đính kèm hoàn tất", status=201)


@router.post("/presigned-url", response_model=APIResponse[Any])
async def get_presigned_url_for_upload(req: PresignedUrlRequest, current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])), db=Depends(get_db)) -> Any:
    if req.is_system and current_user.role not in {Role.AUTHOR, Role.ADMIN}:
        raise HTTPException(status_code=403, detail="Không có quyền tải tệp hệ thống")
    is_temporary = req.is_message_attachment and current_user.ai_tier.upper() == Tier.BASIC.value and current_user.role != Role.ADMIN
    if not req.is_system and not is_temporary:
        await enforce_quota(current_user.id, req.size)
    result = await UploadService.get_presigned_upload_url(req.filename, req.content_type, current_user.id, req.is_system, req.is_message_attachment, is_temporary)
    reservation = {
        "owner_id": current_user.id,
        "filename": req.filename,
        "size": req.size,
        "content_type": req.content_type,
        "is_system": req.is_system,
        "is_message_attachment": req.is_message_attachment,
    }
    await redis.setex(f"cloud:upload:{result['file_path']}", 3600, json.dumps(reservation))
    return APIResponse(data=result, message="Khởi tạo đường dẫn truyền tải bảo mật hoàn tất", status=200)


@router.post("/xac-nhan", response_model=APIResponse[Any], status_code=201)
async def confirm_upload(req: ConfirmUploadRequest, current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])), db=Depends(get_db)) -> Any:
    client = redis.get_client()
    raw = await client.execute_command("GETDEL", f"cloud:upload:{req.file_path}")
    if not raw:
        raise HTTPException(status_code=409, detail="Yêu cầu tải lên không tồn tại hoặc đã được xác nhận")
    reservation = json.loads(raw)
    expected = {
        "owner_id": current_user.id,
        "filename": req.filename,
        "size": req.size,
        "content_type": req.content_type,
        "is_system": req.is_system,
        "is_message_attachment": req.is_message_attachment,
    }
    if reservation != expected:
        raise HTTPException(status_code=400, detail="Thông tin xác nhận tải lên không hợp lệ")
    storage = await get_storage_client()
    try:
        metadata = await storage.head_object(Bucket=get_bucket(req.file_path), Key=req.file_path)
    except Exception:
        raise HTTPException(status_code=400, detail="Không tìm thấy tệp đã tải lên")
    actual_type = (metadata.get("ContentType") or "").split(";", 1)[0].lower()
    if metadata.get("ContentLength") != req.size or actual_type != req.content_type.lower():
        await storage.delete_object(Bucket=get_bucket(req.file_path), Key=req.file_path)
        raise HTTPException(status_code=400, detail="Nội dung tải lên không khớp yêu cầu")
    result = {"url": req.file_path, "filename": req.filename, "size": req.size, "content_type": req.content_type}
    if req.is_system:
        return APIResponse(data=result, message="Xác thực tải lên hệ thống hoàn tất", status=201)
    is_temporary = req.is_message_attachment and current_user.ai_tier.upper() == Tier.BASIC.value and current_user.role != Role.ADMIN
    if is_temporary:
        await database.mongodb[settings.CLOUD_DB_NAME].temp_chat_files.insert_one({
            "owner_id": current_user.id,
            "url": req.file_path,
            "original_filename": req.filename,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=14),
        })
        result["expires_in_days"] = 14
    else:
        await enforce_quota(current_user.id, req.size)
        item = await register_item(result, current_user.id)
        result["item_id"] = item.id
    return APIResponse(data=result, message="Xác thực truyền tải tệp hoàn tất", status=201)


@router.get("/luu-tru/{file_path:path}")
async def get_presigned_download_url(file_path: str, current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER])), db=Depends(get_db)):
    if not await can_download(file_path, current_user.id, current_user.role):
        raise HTTPException(status_code=403, detail="Không có quyền tải xuống tệp này")
    url_data = await UploadService.get_presigned_url(file_path)
    return RedirectResponse(url=url_data["download_url"], status_code=302)


@router.get("/noi-dung/{file_path:path}")
async def get_message_attachment_content(file_path: str, current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER]))):
    if not await can_download(file_path, current_user.id, current_user.role):
        raise HTTPException(status_code=403, detail="Không có quyền tải xuống tệp này")
    content, content_type = await download_file(file_path)
    return Response(content=content, media_type=content_type)


@router.post("/phan-doan", response_model=APIResponse[Any], status_code=201)
async def upload_chunk(file: UploadFile = File(...), upload_id: str = Form(...), chunk_index: int = Form(...), total_chunks: int = Form(...), filename: str = Form(...), current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])), db=Depends(get_db)) -> Any:
    try:
        normalized_id = str(UUID(upload_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Mã phiên tải lên không hợp lệ")
    UploadService.validate_filename(filename, file.content_type or "application/octet-stream")
    if total_chunks < 1 or total_chunks > 1000 or chunk_index < 0 or chunk_index >= total_chunks:
        raise HTTPException(status_code=400, detail="Thông tin phân đoạn không hợp lệ")
    chunk = await UploadService.read_limited(file)
    chunk_dir = Path("storage/chunks") / current_user.id / normalized_id
    chunk_dir.mkdir(parents=True, exist_ok=True)
    chunk_path = chunk_dir / f"chunk_{chunk_index}"
    async with aiofiles.open(chunk_path, "wb") as stream:
        await stream.write(chunk)
    parts = [chunk_dir / f"chunk_{index}" for index in range(total_chunks)]
    if not all(part.is_file() for part in parts):
        return APIResponse(data={"uploaded": chunk_index}, message="Truyền tải phân đoạn hoàn tất", status=200)
    total_size = sum(part.stat().st_size for part in parts)
    if total_size > settings.MAX_UPLOAD_SIZE_BYTES:
        shutil.rmtree(chunk_dir)
        raise HTTPException(status_code=413, detail="Tệp tải lên vượt quá kích thước cho phép")
    await enforce_quota(current_user.id, total_size)
    content = bytearray()
    for part in parts:
        async with aiofiles.open(part, "rb") as stream:
            content.extend(await stream.read())
    from src.core.storage import upload_file

    ext = filename.rsplit(".", 1)[-1].lower()
    content_type = file.content_type or "application/octet-stream"
    path = UploadService.object_path(ext, content_type, current_user.id, False, False)
    try:
        await upload_file(bytes(content), path, content_type)
        result = {"url": path, "filename": filename, "size": total_size, "content_type": content_type}
        item = await register_item(result, current_user.id)
        result["item_id"] = item.id
    finally:
        shutil.rmtree(chunk_dir, ignore_errors=True)
    return APIResponse(data=result, message="Truyền tải tệp tin hoàn tất", status=201)

@router.post("/yeu-cau/{token}", response_model=APIResponse[Any], status_code=201)
async def upload_via_request(
    token: str,
    file: UploadFile = File(...),
    password: Optional[str] = Form(None),
    db=Depends(get_db)
) -> Any:
    from src.services.file_request import FileRequestService
    req_info = await FileRequestService.validate_request(token, password)
    if not req_info or "error" in req_info:
        raise HTTPException(status_code=403, detail="Liên kết không hợp lệ, hết hạn hoặc sai mật khẩu")
    
    size = await file_size(file)
    owner_id = req_info["owner_id"]
    target_folder_id = req_info["target_folder_id"]
    
    await enforce_quota(owner_id, size)
    result = await UploadService.upload_document(file, owner_id=owner_id)
    
    from src.schemas.storage import StorageItemCreate
    item = await StorageService.create_item(
        StorageItemCreate(
            name=result["filename"],
            is_folder=False,
            url=result["url"],
            size=result["size"],
            mime_type=result["content_type"],
            parent_id=target_folder_id
        ),
        owner_id,
    )
    result["item_id"] = item.id
    return APIResponse(data=result, message="Truyền tải tệp tin qua yêu cầu hoàn tất", status=201)
