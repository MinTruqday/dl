from fastapi import APIRouter, Depends, Query

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.domain.contracts import (
    CollaborationConflictResolution,
    CollaborationOperationInput,
    CollaborationPresenceInput,
)
from src.services.collaboration import CollaborationService

router = APIRouter(prefix="/kiem-thu", tags=["Cộng tác thời gian thực"])


@router.put("/du-an/{project_id}/cong-tac/phien")
async def update_collaboration_presence(
    project_id: str,
    payload: CollaborationPresenceInput,
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(await CollaborationService.update_presence(project_id, payload, user))


@router.get("/du-an/{project_id}/cong-tac/hien-dien")
async def list_collaboration_presence(
    project_id: str,
    artifact_type: str = Query(pattern="^(requirement|test_case)$"),
    artifact_id: str = Query(min_length=1, max_length=200),
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(
        await CollaborationService.list_presence(
            project_id, artifact_type, artifact_id, user
        )
    )


@router.post("/du-an/{project_id}/cong-tac/yeu-cau/{artifact_id}/thao-tac")
async def apply_requirement_collaboration_operation(
    project_id: str,
    artifact_id: str,
    payload: CollaborationOperationInput,
    user: CurrentUser = Depends(get_current_user),
):
    return await CollaborationService.apply_operation(
        project_id, "requirement", artifact_id, payload, user
    )


@router.post("/du-an/{project_id}/cong-tac/ca-kiem-thu/{artifact_id}/thao-tac")
async def apply_test_case_collaboration_operation(
    project_id: str,
    artifact_id: str,
    payload: CollaborationOperationInput,
    user: CurrentUser = Depends(get_current_user),
):
    return await CollaborationService.apply_operation(
        project_id, "test_case", artifact_id, payload, user
    )


@router.get("/du-an/{project_id}/cong-tac/xung-dot")
async def list_collaboration_conflicts(
    project_id: str, user: CurrentUser = Depends(get_current_user)
):
    return envelope(await CollaborationService.list_conflicts(project_id, user))


@router.post("/du-an/{project_id}/cong-tac/xung-dot/{conflict_id}/giai-quyet")
async def resolve_collaboration_conflict(
    project_id: str,
    conflict_id: str,
    payload: CollaborationConflictResolution,
    user: CurrentUser = Depends(get_current_user),
):
    value = await CollaborationService.resolve_conflict(project_id, conflict_id, payload, user)
    return envelope(value, revision=value["conflict"]["revision"])
