from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends
from src.services.ingestion import collector as collector_service
from src.schemas.ingestion import Collection
from src.core.dependency import get_current_user, require_role, Role

router = APIRouter(route_class=LoggingRoute, prefix="/thu-thap")

@router.post("/kich-hoat", dependencies=[Depends(require_role([Role.ADMIN]))])
async def trigger_collection(req: Collection, current_user = Depends(get_current_user)):
    return await collector_service.trigger_collection(req)

@router.post("/tam-dung", dependencies=[Depends(require_role([Role.ADMIN]))])
async def stop_collection(current_user = Depends(get_current_user)):
    return await collector_service.stop_collection()

@router.get("/tien-trinh-dang-chay", dependencies=[Depends(require_role([Role.ADMIN]))])
async def get_active_jobs(current_user = Depends(get_current_user)):
    return await collector_service.get_active_jobs()

@router.get("/thong-ke", dependencies=[Depends(require_role([Role.ADMIN]))])
async def get_collector_stats(current_user = Depends(get_current_user)):
    return await collector_service.get_collector_stats()

@router.get("/nhat-ky-hoat-dong", dependencies=[Depends(require_role([Role.ADMIN]))])
async def get_collector_logs(current_user = Depends(get_current_user)):
    return await collector_service.get_collector_logs()
