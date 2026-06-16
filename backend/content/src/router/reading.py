import io
import ipaddress
import socket
import zipfile
import aiohttp
from urllib.parse import urlparse
from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query, HTTPException
from core.dependency import get_current_user, get_db
from src.schemas.library import ProgressUpdate
from src.services.reading import ReadingService

router = APIRouter(prefix="/reading")

@router.get("/history", response_model=APIResponse[Any])
async def get_history(cursor: str = None, limit: int = Query(20), current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await ReadingService.get_reading_history(current_user, cursor, limit, db=db),
        message="Personal reading history trajectory has been successfully retrieved from system records",
    )

@router.post("/progress", response_model=APIResponse[Any])
async def update_progress(data: ProgressUpdate, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await ReadingService.update_progress(data, current_user, db=db),
        message="Current reading progress metrics have been successfully synchronized and updated internally",
    )

@router.get("/documents/{document_id}/search", response_model=APIResponse[Any])
async def search_in_document(document_id: str, q: str = Query(...), current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await ReadingService.search_in_document(document_id, q, current_user, db=db),
        message="Contextual search operation within document content has been successfully executed returning matches",
    )

@router.delete("/history", response_model=APIResponse[Any])
async def clear_reading_history(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await ReadingService.clear_reading_history(current_user, db=db),
        message="Entire reading history profile has been successfully and permanently expunged",
    )

@router.delete("/history/{document_id}", response_model=APIResponse[Any])
async def delete_history_item(document_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await ReadingService.delete_history_item(document_id, current_user, db=db),
        message="Specified reading history chronological entry has been successfully removed from account",
    )

def validate_url_ssrf(url: str):
    parsed = urlparse(url)
    if not parsed.hostname:
        raise HTTPException(status_code=400, detail="Requested structural file path is invalid and cannot be processed operationally")
    try:
        ip = socket.gethostbyname(parsed.hostname)
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
            raise HTTPException(status_code=403, detail="Target domain resolves to restricted internal network address violating security policies")
    except socket.gaierror:
        raise HTTPException(status_code=400, detail="System was entirely unable to successfully resolve provided external domain name")

def is_safe_zip_info(info: zipfile.ZipInfo) -> bool:
    if "" in info.filename or info.filename.startswith("/"):
        return False
    if info.external_attr >> 16 & 40960 == 40960:
        return False
    return True

@router.get("/archive/tree", response_model=APIResponse[Any])
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
                                tree.append({
                                    "path": info.filename,
                                    "name": info.filename.split("/")[-1] if not info.is_dir() else info.filename.split("/")[-2],
                                    "is_dir": info.is_dir(),
                                    "size": info.file_size,
                                })
                        return APIResponse(data=tree, message="Hierarchical directory structure has been successfully extracted and retrieved from archive")
                return APIResponse(data=None, message="Requested archive file is currently unavailable or inaccessible from remote server", status=400)
    except HTTPException as he:
        raise he
    except Exception:
        return APIResponse(data=None, message="System encountered unexpected failure attempting to retrieve hierarchical directory structure", status=500)

@router.get("/archive/content", response_model=APIResponse[Any])
async def get_zip_content(file_url: str = Query(...), path: str = Query(...), db=Depends(get_db)):
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
                                return APIResponse(data=None, message="Requested subfile flagged as potentially unsafe by rigorous internal security system", status=403)
                            file_bytes = z.read(path)
                            try:
                                text = file_bytes.decode("utf-8")
                                return APIResponse(data={"content": text, "type": "text"}, message="Contents of requested embedded file successfully extracted and retrieved internally")
                            except UnicodeDecodeError:
                                return APIResponse(data={"content": "Binary files lack support for direct textual rendering mechanisms", "type": "binary"}, message="Requested file contains dense binary data unsupported by direct text viewers")
                        return APIResponse(data=None, message="Specified individual file could not be securely located within compressed archive", status=404)
    except HTTPException as he:
        raise he
    except Exception:
        return APIResponse(data=None, message="System encountered unexpected structural error attempting process requested archival payload", status=500)