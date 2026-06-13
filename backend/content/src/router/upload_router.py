from typing import Any

from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, Depends, File, Form, UploadFile
from src.router.dependency_router import get_db, require_role
from src.services.upload_service import UploadService

router = APIRouter(prefix="/upload")
import re

from fastapi import HTTPException


async def validate_svg(file: UploadFile):
    if file.filename and file.filename.lower().endswith(".svg"):
        content = await file.read()
        text = content.decode("utf-8", errors="ignore")
        if re.search("<!ENTITY", text, re.IGNORECASE) or re.search(
            "<!DOCTYPE", text, re.IGNORECASE
        ):
            raise HTTPException(
                status_code=400, detail="Tệp SVG chứa định dạng không an toàn"
            )
        await file.seek(0)


@router.post("/image", response_model=APIResponse[Any])
async def upload_image(
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])),
    db=Depends(get_db),
) -> Any:
    await validate_svg(file)
    return APIResponse(
        data=await UploadService.upload_image(file, db=db),
        message="Đã tải hình ảnh lên hệ thống",
        status=201,
    )


@router.post("/document", response_model=APIResponse[Any])
async def upload_document(
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])),
    db=Depends(get_db),
) -> Any:
    return APIResponse(
        data=await UploadService.upload_document(file, db=db),
        message="Đã tải tài liệu lên hệ thống",
        status=201,
    )


@router.post("/file", response_model=APIResponse[Any])
async def upload_asset(
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(
        require_role([RoleEnum.READER, RoleEnum.AUTHOR, RoleEnum.ADMIN])
    ),
    db=Depends(get_db),
) -> Any:
    from fastapi import HTTPException
    from src.services.storage_service import StorageService

    quota = await StorageService.get_storage_quota(current_user.id, db=db)
    if quota["used"] >= quota["limit"]:
        raise HTTPException(
            status_code=400,
            detail="Đã vượt quá hạn mức lưu trữ 1GB vui lòng dọn dẹp bớt tệp tin",
        )
    return APIResponse(
        data=await UploadService.upload_document(file, db=db),
        message="Đã tải tập tin lên hệ thống",
        status=201,
    )


@router.get("/storage/{file_path:path}", response_model=APIResponse[Any])
async def get_presigned_download_url(
    file_path: str,
    current_user: UserInDB = Depends(
        require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER])
    ),
    db=Depends(get_db),
):
    return APIResponse(
        data=await UploadService.get_presigned_url(file_path, db=db),
        message="Đã tạo liên kết tải tập tin",
        status=200,
    )


@router.post("/chunk", response_model=APIResponse[Any])
async def upload_chunk(
    file: UploadFile = File(...),
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    filename: str = Form(...),
    current_user: UserInDB = Depends(
        require_role([RoleEnum.READER, RoleEnum.AUTHOR, RoleEnum.ADMIN])
    ),
    db=Depends(get_db),
) -> Any:
    """Resumable Chunked Upload for flaky networks"""
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

        class MockFile:

            def __init__(self, p, n):
                self.file = open(p, "rb")
                self.filename = n

        mock_file = MockFile(final_path, filename)
        result = await UploadService.upload_document(mock_file, db=db)
        import shutil

        shutil.rmtree(chunk_dir)
        os.remove(final_path)
        return APIResponse(
            data=result, message="Đã tải tập tin lên hệ thống", status=201
        )
    return APIResponse(
        data={"uploaded": chunk_index}, message="Đã tải phân đoạn", status=200
    )
