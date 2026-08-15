from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from src.api.dependency import get_db, require_role
from src.core.dependency import CurrentUser, Role
from src.core.response import APIResponse
from src.schemas.storage import FileRequestCreate, FileRequestResponse
from src.services.file_request import FileRequestService

router = APIRouter(prefix="/luu-tru")

@router.post("/yeu-cau-tai-len", response_model=APIResponse[FileRequestResponse], status_code=201)
async def create_file_request(
    req: FileRequestCreate = Body(...),
    current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])),
    db=Depends(get_db),
):
    from src.services.storage import StorageService
    folder = await StorageService.get_item(req.target_folder_id, current_user.id)
    if not folder or not folder.is_folder:
        raise HTTPException(status_code=400, detail="Thư mục đích không hợp lệ")
        
    result = await FileRequestService.create_request(req, current_user.id)
    if not result:
        raise HTTPException(status_code=500, detail="Không thể tạo liên kết yêu cầu tải lên")
        
    return APIResponse(
        data=result,
        message="Tạo liên kết yêu cầu tải lên hoàn tất",
        status=201
    )

@router.get("/yeu-cau-tai-len/{token}", response_model=APIResponse[Any])
async def validate_file_request(
    token: str,
    password: Optional[str] = Query(default=None),
    db=Depends(get_db),
):
    result = await FileRequestService.validate_request(token, password)
    if not result:
        raise HTTPException(status_code=404, detail="Liên kết yêu cầu tải lên không hợp lệ hoặc đã hết hạn")
    
    if "error" in result:
        raise HTTPException(status_code=403, detail=result["error"])
        
    return APIResponse(
        data=result,
        message="Xác thực liên kết yêu cầu tải lên thành công",
        status=200
    )
