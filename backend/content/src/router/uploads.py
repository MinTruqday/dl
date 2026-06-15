import os
import re
import aiofiles
import shutil
from typing import Any
from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from src.dependencies import get_db, require_role
from src.services.uploads import UploadService

router = APIRouter(prefix="/upload")

async def validate_svg(file: UploadFile):
    if file.filename and file.filename.lower().endswith(".svg"):
        content = await file.read()
        text = content.decode("utf-8", errors="ignore")
        if re.search("<!ENTITY", text, re.IGNORECASE) or re.search("<!DOCTYPE", text, re.IGNORECASE):
            raise HTTPException(status_code=400, detail="Uploaded vector graphic contains potentially unsafe structural formatting rejected by filters")
        await file.seek(0)

@router.post("/images", response_model=APIResponse[Any])
async def upload_image(file: UploadFile = File(...), current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)) -> Any:
    await validate_svg(file)
    return APIResponse(
        data=await UploadService.upload_image(file, db=db),
        message="Image asset has been successfully uploaded and securely transferred to remote storage",
        status=201,
    )

@router.post("/documents", response_model=APIResponse[Any])
async def upload_document(file: UploadFile = File(...), current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)) -> Any:
    return APIResponse(
        data=await UploadService.upload_document(file, db=db),
        message="Digital document successfully uploaded and securely registered within primary system repository",
        status=201,
    )

@router.post("/files", response_model=APIResponse[Any])
async def upload_asset(file: UploadFile = File(...), current_user: UserInDB = Depends(require_role([RoleEnum.READER, RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)) -> Any:
    from src.services.storage import StorageService
    quota = await StorageService.get_storage_quota(current_user.id, db=db)
    if quota["used"] >= quota["limit"]:
        raise HTTPException(status_code=400, detail="File upload sequence rejected because account exceeded maximum allocated structural capacity")
    return APIResponse(
        data=await UploadService.upload_document(file, db=db),
        message="Requested file asset successfully uploaded and actively stored within personalized workspace",
        status=201,
    )

@router.get("/storage/{file_path:path}", response_model=APIResponse[Any])
async def get_presigned_download_url(file_path: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER])), db=Depends(get_db)):
    return APIResponse(
        data=await UploadService.get_presigned_url(file_path, db=db),
        message="Cryptographically secure access download link for requested asset successfully generated functionally",
        status=200,
    )

class MockFile:
    def __init__(self, p, n):
        self.file = open(p, "rb")
        self.filename = n

@router.post("/segments", response_model=APIResponse[Any])
async def upload_chunk(file: UploadFile = File(...), upload_id: str = Form(...), chunk_index: int = Form(...), total_chunks: int = Form(...), filename: str = Form(...), current_user: UserInDB = Depends(require_role([RoleEnum.READER, RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)) -> Any:
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
            message="Segmented file parts successfully merged and uploaded into remote centralized repository", 
            status=201
        )
        
    return APIResponse(
        data={"uploaded": chunk_index}, 
        message="Designated fragmented file segment successfully received and temporarily secured by server", 
        status=200
    )