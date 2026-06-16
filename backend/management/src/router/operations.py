from typing import Any
from core.dependency import get_current_user, get_db, require_role
from core.response import APIResponse
from fastapi import APIRouter, Depends
from src.schemas.management import CampaignRequest, CollectionRequest
from src.services.operations import OperationService
from src.services.users import UserService

router = APIRouter(prefix="/operations")

@router.get("/metrics", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_system_metrics(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_system_telemetry(db=db),
        message="Comprehensive system operational metrics and data have been successfully retrieved",
    )

@router.get("/maintenance", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_maintenance_status(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_maintenance_mode(db=db),
        message="Current system maintenance status has been successfully verified and retrieved",
    )

@router.post("/maintenance", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def toggle_maintenance(enabled: bool, db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.toggle_maintenance_mode(enabled, db=db),
        message="Global system maintenance mode configuration has been successfully updated in database",
    )

@router.post("/backup", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def trigger_backup(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.trigger_backup(db=db),
        message="Comprehensive system data backup process has been successfully initiated and scheduled",
    )

@router.post("/api-key", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def create_api_key(name: str, db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.create_api_key(name, db=db),
        message="New secure application access key has been generated and recorded successfully",
    )

@router.post("/marketing/campaign", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def create_marketing_campaign(payload: CampaignRequest, db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.create_marketing_campaign(payload.model_dump(), db=db),
        message="New marketing promotional campaign has been successfully configured and activated",
        status=201,
    )

@router.get("/settings", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_system_config(db=Depends(get_db)):
    return APIResponse(
        data={},
        message="Global system configuration settings have been successfully retrieved from the database"
    )

@router.get("/health", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_system_health(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_system_health(db=db),
        message="Comprehensive system health and diagnostic report has been successfully generated",
    )

@router.get("/reports", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_admin_reports(db=Depends(get_db)):
    return APIResponse(
        data=await UserService.get_report_queue(status_filter=None, db=db),
        message="Administrative violation reports have been successfully retrieved for staff review",
    )

@router.get("/collectors/stats", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_collector_stats(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_collector_stats(db=db),
        message="Statistical data from external data collection service has been successfully compiled",
    )

@router.post("/collectors/trigger", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def trigger_collection(req: CollectionRequest, db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.trigger_collection(req.source, req.pages, db=db),
        message="External data collection process has been successfully triggered and is running",
    )

@router.post("/collectors/stop", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def stop_collection(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.stop_collection(db=db),
        message="Halt command has been successfully transmitted to external data collection service",
    )

@router.get("/collectors/logs", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_collector_logs(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_collector_logs(db=db),
        message="Operational logs from data collection service have been successfully retrieved",
    )

@router.get("/collectors/active-jobs", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_active_collector_jobs(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_active_collector_jobs(db=db),
        message="List of active background tasks in data collection service retrieved successfully",
    )

@router.post("/users/{user_id}/shadowban", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def shadowban_user(payload: Any, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.bulk_update_shadowban(payload.user_ids, payload.status, current_user, db=db),
        message="Visibility restriction protocol has been successfully applied to specified account",
    )

@router.post("/users/{user_id}/kyc/{status}", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def verify_kyc(payload: Any, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.bulk_verify_kyc(payload.user_ids, payload.status, current_user, db=db),
        message="Identity verification profile has been successfully processed and updated",
    )

@router.get("/storage/stats", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_minio_stats(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_minio_stats(db=db),
        message="Comprehensive storage usage statistics successfully retrieved from object storage service",
    )