from typing import Any
from fastapi import APIRouter, Depends, File, Form, UploadFile
from src.core.response import APIResponse
from src.api.dependency import get_db, require_role
from src.core.dependency import CurrentUser, Role
from src.services.chunk import ChunkService
from src.services.file import FileService
from src.services.upload import UploadService
from src.schemas.storage import StorageItemCreate

router = APIRouter(prefix="/phan-doan")

@router.post("", response_model=APIResponse[Any], status_code=201)
async def upload_chunk(
    file: UploadFile = File(...),
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    filename: str = Form(...),
    current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])),
    db=Depends(get_db),
) -> Any:
    content_type = file.content_type or "application/octet-stream"
    UploadService.validate_filename(filename, content_type)
    content = await UploadService.read_limited(file)
    res = await ChunkService.save_chunk(
        upload_id=upload_id,
        chunk_index=chunk_index,
        total_chunks=total_chunks,
        filename=filename,
        content=content,
        content_type=content_type,
        user_id=current_user.id,
    )
    if res.get("is_complete"):
        item = await FileService.create_file_record(
            StorageItemCreate(
                name=res["filename"],
                is_folder=False,
                url=res["url"],
                size=res["size"],
                mime_type=res["content_type"],
            ),
            current_user.id,
        )
        res["item_id"] = item.id
        return APIResponse(data=res, message="Truyền tải phân đoạn và hợp nhất tệp hoàn tất", status=201)
    return APIResponse(data=res, message="Truyền tải phân đoạn hoàn tất", status=200)
