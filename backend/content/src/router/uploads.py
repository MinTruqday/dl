import os
import re
import aiofiles
import shutil
from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from core.dependency import get_db, require_role
from src.services.uploads import UploadService

router = APIRouter(prefix="/tai-len")

async def validate_svg(file: UploadFile):
    if file.filename and file.filename.lower().endswith(".svg"):
        content = await file.read()
        text = content.decode("utf-8", errors="ignore")
        if re.search("<!ENTITY", text, re.IGNORECASE) or re.search("<!DOCTYPE", text, re.IGNORECASE):
            raise HTTPException(status_code=400, detail="Lỗi truy xuất cơ sở dữ liệu hệ thống")
        await file.seek(0)

@router.post("/hinh-anh", response_model=APIResponse[Any])
async def upload_image(file: UploadFile = File(...), current_user: dict = Depends(require_role(["author", "admin"])), db=Depends(get_db)) -> Any:
    await validate_svg(file)
    return APIResponse(
        data=await UploadService.upload_image(file, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=201,
    )

@router.post("/tai-lieu", response_model=APIResponse[Any])
async def upload_document(file: UploadFile = File(...), current_user: dict = Depends(require_role(["author", "admin"])), db=Depends(get_db)) -> Any:
    return APIResponse(
        data=await UploadService.upload_document(file, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=201,
    )

@router.post("/tap-tin", response_model=APIResponse[Any])
async def upload_asset(file: UploadFile = File(...), current_user: dict = Depends(require_role(["reader", "author", "admin"])), db=Depends(get_db)) -> Any:
    from src.services.storage import StorageService
    quota = await StorageService.get_storage_quota(current_user.get("id"), db=db)
    if quota["used"] >= quota["limit"]:
        raise HTTPException(status_code=400, detail="Lỗi xử lý tài khoản")
    return APIResponse(
        data=await UploadService.upload_document(file, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=201,
    )

@router.get("/luu-tru/{file_path:path}", response_model=APIResponse[Any])
async def get_presigned_download_url(file_path: str, current_user: dict = Depends(require_role(["author", "admin", "reader"])), db=Depends(get_db)):
    return APIResponse(
        data=await UploadService.get_presigned_url(file_path, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )

class MockFile:
    def __init__(self, p, n):
        self.file = open(p, "rb")
        self.filename = n

@router.post("/phan-doan", response_model=APIResponse[Any])
async def upload_chunk(file: UploadFile = File(...), upload_id: str = Form(...), chunk_index: int = Form(...), total_chunks: int = Form(...), filename: str = Form(...), current_user: dict = Depends(require_role(["reader", "author", "admin"])), db=Depends(get_db)) -> Any:
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
                async with aiofiles.open(os.path.join(chunk_dir, f"chunk_{i}"), "rb") as infile:
                    await outfile.write(await infile.read())
                    
        mock_file = MockFile(final_path, filename)
        result = await UploadService.upload_document(mock_file, db=db)
        shutil.rmtree(chunk_dir)
        os.remove(final_path)
        return APIResponse(
            data=result, 
            message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công", 
            status=201
        )
        
    return APIResponse(
        data={"uploaded": chunk_index}, 
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công", 
        status=200
    )