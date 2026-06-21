from typing import Any, List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from src.api.system_dependency import get_current_user, get_db
from src.schemas.personal_library import PinnedDocumentRequest, ProgressUpdate
from src.services.reading_progress import ReadingProgress

from core.response import APIResponse
from core.dependency import CurrentUser, RoleEnum

router = APIRouter(prefix="/doc-hieu")


@router.get("/lich-su", response_model=APIResponse[Any])
async def get_history(
    cursor: str = None,
    limit: int = Query(20),
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await ReadingProgress.get_reading_history(
            current_user, cursor, limit, db=db
        ),
        message="Lấy lịch sử đọc thành công",
    )


@router.post("/tien-do", response_model=APIResponse[Any])
async def update_progress(
    data: ProgressUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await ReadingProgress.update_progress(data, current_user, db=db),
        message="Đồng bộ tiến độ đọc thành công",
    )


@router.get("/tai-lieu/{document_id}/tim-kiem", response_model=APIResponse[Any])
async def search_in_document(
    document_id: str,
    q: str = Query(...),
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await ReadingProgress.search_in_document(
            document_id, q, current_user, db=db
        ),
        message="Tìm kiếm trong tài liệu thành công",
    )


@router.delete("/lich-su", response_model=APIResponse[Any])
async def clear_reading_history(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await ReadingProgress.clear_reading_history(current_user, db=db),
        message="Xóa toàn bộ lịch sử đọc thành công",
    )


@router.delete("/lich-su/{document_id}", response_model=APIResponse[Any])
async def delete_history_item(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await ReadingProgress.delete_history_item(document_id, current_user, db=db),
        message="Xóa lịch sử đọc thành công",
    )


import io
import ipaddress
import socket
import zipfile
from urllib.parse import urlparse

import aiohttp
from fastapi import HTTPException


def validate_url_ssrf(url: str):
    parsed = urlparse(url)
    if not parsed.hostname:
        raise HTTPException(status_code=400, detail="Đường dẫn tệp không hợp lệ")
    try:
        ip = socket.gethostbyname(parsed.hostname)
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
            raise HTTPException(
                status_code=403,
                detail="Không thể truy cập tên miền nội bộ",
            )
    except socket.gaierror:
        raise HTTPException(status_code=400, detail="Lỗi phân giải tên miền")


def is_safe_zip_info(info: zipfile.ZipInfo) -> bool:
    if "" in info.filename or info.filename.startswith("/"):
        return False
    if info.external_attr >> 16 & 40960 == 40960:
        return False
    return True


@router.get("/luu-tru/cay-thu-muc", response_model=APIResponse[Any])
async def get_zip_tree(file_url: str = Query(...), db=Depends(get_db)):
    try:
        validate_url_ssrf(file_url)
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    with zipfile.ZipFile(io.BytesIO(content)) as z:
                        tree = []
                        for info in z.infolist():
                            if is_safe_zip_info(info):
                                tree.append(
                                    {
                                        "path": info.filename,
                                        "name": (
                                            info.filename.split("/")[-1]
                                            if not info.is_dir()
                                            else info.filename.split("/")[-2]
                                        ),
                                        "is_dir": info.is_dir(),
                                        "size": info.file_size,
                                    }
                                )
                        return APIResponse(
                            data=tree, message="Lấy cấu trúc thư mục thành công"
                        )
                else:
                    return APIResponse(
                        data=None,
                        message="Tệp tin không khả dụng từ máy chủ",
                        status=400,
                    )
    except HTTPException as he:
        raise he
    except Exception:
        return APIResponse(data=None, message="Lỗi tải cấu trúc thư mục", status=500)


@router.get("/luu-tru/noi-dung", response_model=APIResponse[Any])
async def get_zip_content(
    file_url: str = Query(...), path: str = Query(...), db=Depends(get_db)
):
    try:
        validate_url_ssrf(file_url)
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    with zipfile.ZipFile(io.BytesIO(content)) as z:
                        if path in z.namelist():
                            info = z.getinfo(path)
                            if not is_safe_zip_info(info):
                                return APIResponse(
                                    data=None,
                                    message="Tệp có rủi ro bảo mật",
                                    status=403,
                                )
                            file_bytes = z.read(path)
                            try:
                                text = file_bytes.decode("utf-8")
                                return APIResponse(
                                    data={"content": text, "type": "text"},
                                    message="Trích xuất nội dung tệp thành công",
                                )
                            except UnicodeDecodeError:
                                return APIResponse(
                                    data={
                                        "content": "Binary files do not support direct viewing",
                                        "type": "binary",
                                    },
                                    message="Không thể xem trực tiếp tệp nhị phân",
                                )
                        return APIResponse(
                            data=None,
                            message="Không tìm thấy tệp trong thư mục nén",
                            status=404,
                        )
    except HTTPException as he:
        raise he
    except Exception:
        return APIResponse(data=None, message="Lỗi xử lý tệp nén", status=500)
