from fastapi import APIRouter, Depends
from fastapi.responses import Response

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.domain.contracts import (
    AutomationScriptApproval,
    AutomationScriptGenerateInput,
    AutomationScriptPatch,
)
from src.services.automation_script import AutomationScriptService

router = APIRouter(prefix="/kiem-thu", tags=["Kịch bản tự động hóa"])


@router.get("/du-an/{project_id}/ban-nhap-kich-ban-tu-dong")
async def list_automation_script_drafts(
    project_id: str, user: CurrentUser = Depends(get_current_user)
):
    return envelope(await AutomationScriptService.list(project_id, user))


@router.get("/ban-nhap-kich-ban-tu-dong/{draft_id}")
async def get_automation_script_draft(
    draft_id: str, user: CurrentUser = Depends(get_current_user)
):
    value = await AutomationScriptService.get(draft_id, user)
    return envelope(value, revision=value["revision"])


@router.post("/du-an/{project_id}/ai/ban-nhap-kich-ban-tu-dong", status_code=201)
async def generate_automation_script_draft(
    project_id: str,
    payload: AutomationScriptGenerateInput,
    user: CurrentUser = Depends(get_current_user),
):
    value, metadata = await AutomationScriptService.generate(project_id, payload, user)
    return envelope(value, revision=value["revision"], **metadata)


@router.patch("/ban-nhap-kich-ban-tu-dong/{draft_id}")
async def update_automation_script_draft(
    draft_id: str,
    payload: AutomationScriptPatch,
    user: CurrentUser = Depends(get_current_user),
):
    value = await AutomationScriptService.update(draft_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/ban-nhap-kich-ban-tu-dong/{draft_id}/phe-duyet")
async def approve_automation_script_draft(
    draft_id: str,
    payload: AutomationScriptApproval,
    user: CurrentUser = Depends(get_current_user),
):
    value = await AutomationScriptService.approve(draft_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.get("/ban-nhap-kich-ban-tu-dong/{draft_id}/xuat")
async def export_automation_script_draft(
    draft_id: str, user: CurrentUser = Depends(get_current_user)
):
    source, filename = await AutomationScriptService.export(draft_id, user)
    return Response(
        content=source,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
