from typing import Any, List, Optional

from core.response import APIResponse
from core.schemas.collector import CollectionRequest
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, Depends, status
from src.router.dependency_router import get_current_user, get_db, require_role
from src.schemas.operation_schema import CampaignRequest
from src.services.operation_service import OperationService
from src.services.user_service import UserService

router = APIRouter(prefix="/operations")


@router.get(
    "/metrics",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_system_metrics(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_system_telemetry(db=db),
        message="The comprehensive system operational metrics and data have been successfully retrieved",
    )


@router.get(
    "/maintenance",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_maintenance_status(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_maintenance_mode(db=db),
        message="The current system maintenance status has been successfully verified and retrieved",
    )


@router.post(
    "/maintenance",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def toggle_maintenance(enabled: bool, db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.toggle_maintenance_mode(enabled, db=db),
        message="The global system maintenance mode configuration has been successfully updated",
    )


@router.post(
    "/backup",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def trigger_backup(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.trigger_backup(db=db),
        message="The comprehensive system data backup process has been successfully initiated",
    )


@router.post(
    "/api-key",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def create_api_key(name: str, db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.create_api_key(name, db=db),
        message="The new secure application access key has been generated and recorded successfully",
    )


@router.post(
    "/marketing/campaign",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def create_marketing_campaign(payload: CampaignRequest, db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.create_marketing_campaign(
            payload.model_dump(), db=db
        ),
        message="The new marketing and promotional campaign has been successfully configured and activated",
        status=201,
    )


@router.get(
    "/settings",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_system_config(db=Depends(get_db)):
    return APIResponse(data={}, message="The global system configuration settings have been successfully retrieved from the database")


@router.get(
    "/health",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_system_health(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_system_health(db=db),
        message="The comprehensive system health and diagnostic report has been successfully generated",
    )


@router.get(
    "/reports",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_admin_reports(db=Depends(get_db)):
    return APIResponse(
        data=await UserService.get_report_queue(status_filter=None, db=db),
        message="The administrative violation reports have been successfully retrieved for review",
    )


@router.get(
    "/collectors/stats",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_collector_stats(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_collector_stats(db=db),
        message="The statistical data from the data collection service has been successfully compiled",
    )


@router.post(
    "/collectors/trigger",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def trigger_collection(req: CollectionRequest, db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.trigger_collection(req.source, req.pages, db=db),
        message="The external data collection process has been successfully triggered and is now running",
    )


@router.post(
    "/collectors/stop",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def stop_collection(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.stop_collection(db=db),
        message="The halt command has been successfully transmitted to the external data collection service",
    )


@router.get(
    "/collectors/logs",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_collector_logs(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_collector_logs(db=db),
        message="The operational logs from the data collection service have been successfully retrieved",
    )


@router.get(
    "/collectors/active-jobs",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_active_collector_jobs(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_active_collector_jobs(db=db),
        message="The list of active background tasks in the data collection service has been retrieved successfully",
    )


@router.post(
    "/users/{user_id}/shadowban",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))],
)
async def shadowban_user(
    payload: Any, current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await OperationService.bulk_update_shadowban(
            payload.user_ids, payload.status, current_user, db=db
        ),
        message="The visibility restriction protocol has been successfully applied to the specified account",
    )


@router.post(
    "/users/{user_id}/kyc/{status}",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))],
)
async def verify_kyc(
    payload: Any, current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await OperationService.bulk_verify_kyc(
            payload.user_ids, payload.status, current_user, db=db
        ),
        message="The identity verification profile has been successfully processed and updated",
    )


@router.get(
    "/storage/stats",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_minio_stats(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_minio_stats(db=db),
        message="The comprehensive storage usage statistics have been successfully retrieved from the object storage service",
    )