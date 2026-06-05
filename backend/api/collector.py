from typing import Any, Optional
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query
from models.user import UserInDB, RoleEnum
from api.dependency import require_role
from services.collector import CollectorService
from models.collector import CollectionRequest
from pydantic import BaseModel
router = APIRouter(prefix='/thu-thap')

@router.post('/kich-hoat', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def trigger_collection(req: CollectionRequest, db=Depends(get_db)):
    return APIResponse(data=await CollectorService.trigger_collection(req.source, req.pages, db=db), message='Yêu cầu thu thập dữ liệu đã được gửi đi', status=202)

@router.post('/dung', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def stop_collection(db=Depends(get_db)):
    return APIResponse(data=await CollectorService.stop_collection(db=db), message='Đã hủy bỏ toàn bộ quá trình thu thập', status=200)

@router.get('/thong-ke', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_collector_stats(db=Depends(get_db)):
    return APIResponse(data=await CollectorService.get_collector_stats(db=db), message='Lấy số liệu thống kê thu thập thành công', status=200)
import os

@router.get('/logs', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_collector_logs(db=Depends(get_db)):
    log_file = 'logs/backend.log'
    logs = []
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            lines = f.readlines()
            filtered_lines = []
            whitelist = ['pipelines.nxbgd', 'pipelines.anna', 'pipelines.nxbst', 'pipelines.ctan', 'services.collector', '[NXBGD', '[NXBST', '[CTAN', '[Anna', 'Collector']
            for line in lines:
                if any((kw.lower() in line.lower() for kw in whitelist)):
                    filtered_lines.append(line)
            logs = filtered_lines[-50:]
    return APIResponse(data=logs, message='Lấy log thành công', status=200)