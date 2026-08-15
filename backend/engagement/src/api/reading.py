import io
import zipfile
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import urlparse
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from src.core.response import APIResponse
from src.core.infrastructure.configuration import settings
from src.api.dependency import get_current_user, get_db, CurrentUser
from src.schemas.reading import ProgressUpdate
from src.services.reading import ReadingService

router = APIRouter(prefix="/doc-hieu")

@router.get("/lich-su", response_model=APIResponse[Any])
async def get_history(
    cursor: str = None,
    limit: int = Query(20),
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await ReadingService.get_reading_history(
            current_user, cursor, limit
        ),
        message="Trích xuất dữ liệu lịch sử đọc hoàn tất",
    )

@router.post("/tien-do", response_model=APIResponse[Any])
async def update_progress(
    data: ProgressUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await ReadingService.update_progress(data, current_user),
        message="Đồng bộ hóa tiến trình đọc tài liệu hoàn tất",
    )

@router.get("/tai-lieu/{document_id}/tim-kiem", response_model=APIResponse[Any])
async def search_in_document(
    document_id: str,
    q: str = Query(...),
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await ReadingService.search_in_document(
            document_id, q, current_user
        ),
        message="Thực hiện tìm kiếm nội dung trong tài liệu hoàn tất",
    )

@router.delete("/lich-su", response_model=APIResponse[Any])
async def clear_reading_history(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await ReadingService.clear_reading_history(current_user),
        message="Đã xóa toàn bộ dữ liệu lịch sử đọc khỏi hệ thống",
    )

@router.delete("/lich-su/{document_id}", response_model=APIResponse[Any])
async def delete_history_item(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await ReadingService.delete_history_item(document_id, current_user),
        message="Xóa mục lịch sử đọc hoàn tất",
    )

def normalize_storage_url(url: str) -> str:
    parsed = urlparse(url)
    internal = urlparse(settings.MINIO_ENDPOINT)
    public = urlparse(settings.MINIO_PUBLIC_URL) if settings.MINIO_PUBLIC_URL else None
    allowed_hosts = {internal.hostname}
    if public and public.hostname:
        allowed_hosts.add(public.hostname)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.hostname not in allowed_hosts or parsed.username or parsed.password:
        raise HTTPException(status_code=400, detail="Đường dẫn tệp tin cung cấp không hợp lệ")
    return f"{settings.MINIO_ENDPOINT.rstrip('/')}{parsed.path}" + (f"?{parsed.query}" if parsed.query else "")

async def download_zip(url: str) -> bytes:
    target = normalize_storage_url(url)
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=False) as client:
        response = await client.get(target)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Tệp tin yêu cầu không khả dụng")
        if len(response.content) > 100 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Tệp nén vượt quá dung lượng xử lý cho phép")
        return response.content

def is_safe_zip_info(info: zipfile.ZipInfo) -> bool:
    path = PurePosixPath(info.filename)
    if info.filename.startswith("/") or ".." in path.parts or info.file_size > 20 * 1024 * 1024:
        return False
    if info.external_attr >> 16 & 40960 == 40960:
        return False
    return True

@router.get("/luu-tru/cay-thu-muc", response_model=APIResponse[Any])
async def get_zip_tree(file_url: str = Query(...), current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)):
    try:
        content = await download_zip(file_url)
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            if sum(info.file_size for info in z.infolist()) > 200 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="Nội dung giải nén vượt quá dung lượng cho phép")
            tree = []
            for info in z.infolist():
                if is_safe_zip_info(info):
                    tree.append({"path": info.filename, "name": PurePosixPath(info.filename.rstrip("/")).name, "is_dir": info.is_dir(), "size": info.file_size})
            return APIResponse(data=tree, message="Trích xuất cấu trúc tệp nén hoàn tất")
    except HTTPException as he:
        raise he
    except (zipfile.BadZipFile, OSError):
        raise HTTPException(status_code=400, detail="Tệp nén không hợp lệ")

@router.get("/luu-tru/noi-dung", response_model=APIResponse[Any])
async def get_zip_content(
    file_url: str = Query(...), path: str = Query(...), current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    try:
        content = await download_zip(file_url)
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            if path not in z.namelist():
                raise HTTPException(status_code=404, detail="Không tìm thấy tệp trong tệp nén")
            info = z.getinfo(path)
            if not is_safe_zip_info(info) or info.is_dir():
                raise HTTPException(status_code=403, detail="Tệp chứa nội dung có rủi ro bảo mật")
            file_bytes = z.read(path)
            try:
                text = file_bytes.decode("utf-8")
                return APIResponse(data={"content": text, "type": "text"}, message="Trích xuất nội dung tệp tin hoàn tất")
            except UnicodeDecodeError:
                return APIResponse(data={"content": "Binary files do not support direct viewing", "type": "binary"}, message="Định dạng tệp nhị phân không hỗ trợ xem trực tiếp")
    except HTTPException as he:
        raise he
    except (zipfile.BadZipFile, OSError):
        raise HTTPException(status_code=400, detail="Tệp nén không hợp lệ")
