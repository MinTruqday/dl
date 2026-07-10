from typing import Any, List

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from src.api.dependency import get_current_user, get_db
from src.schemas.library import PinnedDocumentRequest, ProgressUpdate
from src.services.reading import ReadingService

from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(route_class=LoggingRoute, prefix="/doc-hieu")

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
        raise HTTPException(status_code=400, detail="Đường dẫn tệp tin cung cấp không hợp lệ")
    try:
        ip = socket.gethostbyname(parsed.hostname)
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
            raise HTTPException(
                status_code=403,
                detail="Yêu cầu bị từ chối do cố gắng truy cập mạng nội bộ hệ thống",
            )
    except socket.gaierror as e:
        raise HTTPException(status_code=400, detail="Hệ thống không thể phân giải tên miền yêu cầu")

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
                            data=tree, message="Trích xuất cấu trúc tệp nén hoàn tất"
                        )
                else:
                    return APIResponse(
                        data=None,
                        message="Tệp tin yêu cầu không khả dụng hoặc không tồn tại trên máy chủ",
                        status=400,
                    )
    except HTTPException as he:
        raise he
    except Exception as e:
        return APIResponse(data=None, message="Hệ thống gặp sự cố trong quá trình phân tích cấu trúc tệp nén", status=500)

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
                                    message="Hệ thống phát hiện tệp tin chứa nội dung có rủi ro bảo mật",
                                    status=403,
                                )
                            file_bytes = z.read(path)
                            try:
                                text = file_bytes.decode("utf-8")
                                return APIResponse(
                                    data={"content": text, "type": "text"},
                                    message="Trích xuất nội dung tệp tin hoàn tất",
                                )
                            except UnicodeDecodeError:
                                return APIResponse(
                                    data={
                                        "content": "Binary files do not support direct viewing",
                                        "type": "binary",
                                    },
                                    message="Định dạng tệp nhị phân không hỗ trợ xem trực tiếp",
                                )
                        return APIResponse(
                            data=None,
                            message="Hệ thống không tìm thấy tệp tin được yêu cầu trong tệp nén",
                            status=404,
                        )
    except HTTPException as he:
        raise he
    except Exception as e:
        return APIResponse(data=None, message="Hệ thống gặp sự cố trong quá trình xử lý tệp nén", status=500)
