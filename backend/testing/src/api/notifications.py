from fastapi import APIRouter, Depends, Query

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.domain.contracts import (
    NotificationWatchInput,
    ProjectNotificationPreferencePatch,
    ProjectNotificationRulePatch,
)
from src.services.project_notification import ProjectNotificationService

router = APIRouter(prefix="/kiem-thu", tags=["Thông báo dự án"])


@router.get("/du-an/{project_id}/thong-bao/theo-doi")
async def list_notification_watches(
    project_id: str,
    artifact_type: str = Query(default="", max_length=40),
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(await ProjectNotificationService.list_watches(project_id, artifact_type, user))


@router.put("/du-an/{project_id}/thong-bao/theo-doi/{artifact_type}/{artifact_id}")
async def set_notification_watch(
    project_id: str,
    artifact_type: str,
    artifact_id: str,
    payload: NotificationWatchInput,
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(
        await ProjectNotificationService.set_watch(
            project_id, artifact_type, artifact_id, payload, user
        )
    )


@router.get("/du-an/{project_id}/thong-bao/quy-tac")
async def get_project_notification_rules(
    project_id: str, user: CurrentUser = Depends(get_current_user)
):
    value = await ProjectNotificationService.get_rules(project_id, user)
    return envelope(value, revision=value["revision"])


@router.patch("/du-an/{project_id}/thong-bao/quy-tac")
async def update_project_notification_rules(
    project_id: str,
    payload: ProjectNotificationRulePatch,
    user: CurrentUser = Depends(get_current_user),
):
    value = await ProjectNotificationService.update_rules(project_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.get("/du-an/{project_id}/thong-bao/tuy-chon")
async def get_project_notification_preferences(
    project_id: str, user: CurrentUser = Depends(get_current_user)
):
    value = await ProjectNotificationService.get_preferences(project_id, user)
    return envelope(value, revision=value["revision"])


@router.patch("/du-an/{project_id}/thong-bao/tuy-chon")
async def update_project_notification_preferences(
    project_id: str,
    payload: ProjectNotificationPreferencePatch,
    user: CurrentUser = Depends(get_current_user),
):
    value = await ProjectNotificationService.update_preferences(project_id, payload, user)
    return envelope(value, revision=value["revision"])
