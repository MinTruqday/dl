from fastapi import APIRouter, Depends
from src.services import collector as collector_service
from src.schemas.collector import CollectionRequest
from core.dependency import get_current_user, require_role, RoleEnum

router = APIRouter(prefix="/thu-thap")

@router.post("/kich-hoat", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def trigger_collection(req: CollectionRequest, current_user = Depends(get_current_user)):
    return await collector_service.trigger_collection(req)

@router.post("/tam-dung", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def stop_collection(current_user = Depends(get_current_user)):
    return await collector_service.stop_collection()

@router.get("/tien-trinh-dang-chay", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_active_jobs(current_user = Depends(get_current_user)):
    return await collector_service.get_active_jobs()

@router.get("/thong-ke", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_collector_stats(current_user = Depends(get_current_user)):
    return await collector_service.get_collector_stats()

@router.get("/nhat-ky-hoat-dong", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_collector_logs(current_user = Depends(get_current_user)):
    return await collector_service.get_collector_logs()
