import re
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from src.api.system_dependency import get_db, require_role
from src.services.file_upload import FileUpload

from core.api_response import APIResponse
from core.system_dependency import CurrentUser, RoleEnum

router = APIRouter(prefix="/tai-len")


async def validate_svg(file: UploadFile):
    if file.filename and file.filename.lower().endswith(".svg"):
        content = await file.read()
        text = content.decode("utf-8", errors="ignore")
        if re.search("<!ENTITY", text, re.IGNORECASE) or re.search(
            "<!DOCTYPE", text, re.IGNORECASE
        ):
            raise HTTPException(
                status_code=400, detail="Từ chối tệp đồ họa vector do có rủi ro"
            )
        await file.seek(0)


@router.post("/hinh-anh", response_model=APIResponse[Any])
async def upload_image(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])),
    db=Depends(get_db),
) -> Any:
    await validate_svg(file)
    return APIResponse(
        data=await FileUpload.upload_image(file, db=db),
        message="Tải lên hình ảnh thành công",
        status=201,
    )


@router.post("/tai-lieu", response_model=APIResponse[Any])
async def upload_document(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])),
    db=Depends(get_db),
) -> Any:
    return APIResponse(
        data=await FileUpload.upload_document(file, db=db),
        message="Tải lên và lưu trữ tài liệu thành công",
        status=201,
    )


@router.post("/tap-tin", response_model=APIResponse[Any])
async def upload_asset(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(
        require_role([RoleEnum.READER, RoleEnum.AUTHOR, RoleEnum.ADMIN])
    ),
    db=Depends(get_db),
) -> Any:
    from src.services.file_storage import StorageOperations

    quota = await StorageOperations.get_storage_quota(current_user.id, db=db)
    if quota["used"] >= quota["limit"]:
        raise HTTPException(
            status_code=400,
            detail="Lỗi tải lên do vượt giới hạn lưu trữ",
        )
    return APIResponse(
        data=await FileUpload.upload_document(file, db=db),
        message="Tải lên tệp tin thành công",
        status=201,
    )


@router.get("/storage/{file_path:path}", response_model=APIResponse[Any])
async def get_presigned_download_url(
    file_path: str,
    current_user: CurrentUser = Depends(
        require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER])
    ),
    db=Depends(get_db),
):
    return APIResponse(
        data=await FileUpload.get_presigned_url(file_path, db=db),
        message="Tạo liên kết tải xuống bảo mật thành công",
        status=200,
    )


@router.post("/phan-doan", response_model=APIResponse[Any])
async def upload_chunk(
    file: UploadFile = File(...),
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    filename: str = Form(...),
    current_user: CurrentUser = Depends(
        require_role([RoleEnum.READER, RoleEnum.AUTHOR, RoleEnum.ADMIN])
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

        class MockFile:

            def __init__(self, p, n):
                self.file = open(p, "rb")
                self.filename = n

        mock_file = MockFile(final_path, filename)
        result = await FileUpload.upload_document(mock_file, db=db)
        import shutil

        shutil.rmtree(chunk_dir)
        os.remove(final_path)
        return APIResponse(
            data=result, message="Tải lên tệp tin thành công", status=201
        )
    return APIResponse(
        data={"uploaded": chunk_index},
        message="Tải lên tệp tạm thời thành công",
        status=200,
    )
