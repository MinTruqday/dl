from typing import Any, List
from fastapi import APIRouter, Depends, Query
from api.dependency import get_db, get_current_user
from models.user import UserInDB
from models.library import TypographyRequest, ProgressUpdate, ReadingGoalCreate, PinnedDocumentRequest
from core.response import APIResponse
from services.reading import ReadingService
from pydantic import BaseModel
router = APIRouter(prefix='/doc')

@router.get('/lich-su', response_model=APIResponse[Any])
async def get_history(cursor: str=None, limit: int=Query(20), current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await ReadingService.get_reading_history(current_user, cursor, limit, db=db), message='Lấy lịch sử đọc thành công')

@router.post('/tien-do', response_model=APIResponse[Any])
async def update_progress(data: ProgressUpdate, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await ReadingService.update_progress(data, current_user, db=db), message='Cập nhật tiến độ thành công')



@router.post('/muc-tieu', response_model=APIResponse[Any])
async def set_reading_goal(data: ReadingGoalCreate, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await ReadingService.set_reading_goal(data, current_user, db=db), message='Thiết lập mục tiêu thành công', status=201)

@router.get('/muc-tieu', response_model=APIResponse[Any])
async def get_reading_goal(current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await ReadingService.get_reading_goal(current_user, db=db), message='Lấy thông tin mục tiêu thành công')

@router.put('/trinh-bay', response_model=APIResponse[Any])
async def update_typography(data: TypographyRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await ReadingService.update_typography(data, current_user, db=db), message='Cập nhật hiển thị thành công')

@router.get('/tai-lieu/{document_id}/tim-kiem', response_model=APIResponse[Any])
async def search_in_document(document_id: str, q: str=Query(...), current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await ReadingService.search_in_document(document_id, q, current_user, db=db), message='Tìm kiếm trong tài liệu thành công')

@router.delete('/lich-su', response_model=APIResponse[Any])
async def clear_reading_history(current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await ReadingService.clear_reading_history(current_user, db=db), message='Xóa toàn bộ lịch sử đọc thành công')

@router.delete('/lich-su/{document_id}', response_model=APIResponse[Any])
async def delete_history_item(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await ReadingService.delete_history_item(document_id, current_user, db=db), message='Xóa mục lịch sử đọc thành công')
import aiohttp
import zipfile
import io
import socket
from urllib.parse import urlparse
import ipaddress
from fastapi import HTTPException

def validate_url_ssrf(url: str):
    parsed = urlparse(url)
    if not parsed.hostname:
        raise HTTPException(status_code=400, detail='Invalid URL')
    try:
        ip = socket.gethostbyname(parsed.hostname)
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
            raise HTTPException(status_code=403, detail='Tên miền phân giải ra IP nội bộ bị cấm (SSRF Protection).')
    except socket.gaierror:
        raise HTTPException(status_code=400, detail='Cannot resolve hostname')

def is_safe_zip_info(info: zipfile.ZipInfo) -> bool:
    if '..' in info.filename or info.filename.startswith('/'):
        return False
    if info.external_attr >> 16 & 40960 == 40960:
        return False
    return True

@router.get('/cay-thu-muc-zip', response_model=APIResponse[Any])
async def get_zip_tree(file_url: str=Query(...), db=Depends(get_db)):
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
                                tree.append({'path': info.filename, 'name': info.filename.split('/')[-1] if not info.is_dir() else info.filename.split('/')[-2], 'is_dir': info.is_dir(), 'size': info.file_size})
                        return APIResponse(data=tree, message='Lấy cây thư mục thành công')
                else:
                    return APIResponse(data=None, message='Không thể tải file', status=400)
    except HTTPException as he:
        raise he
    except Exception as e:
        return APIResponse(data=None, message=str(e), status=500)

@router.get('/noi-dung-zip', response_model=APIResponse[Any])
async def get_zip_content(file_url: str=Query(...), path: str=Query(...), db=Depends(get_db)):
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
                                return APIResponse(data=None, message='Tệp tin không an toàn', status=403)
                            file_bytes = z.read(path)
                            try:
                                text = file_bytes.decode('utf-8')
                                return APIResponse(data={'content': text, 'type': 'text'}, message='Thành công')
                            except UnicodeDecodeError:
                                return APIResponse(data={'content': 'Binary file cannot be displayed.', 'type': 'binary'}, message='Thành công')
                        return APIResponse(data=None, message='Không tìm thấy tệp', status=404)
    except HTTPException as he:
        raise he
    except Exception as e:
        return APIResponse(data=None, message=str(e), status=500)