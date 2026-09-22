import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pymongo.errors import DuplicateKeyError

from src.core.auth import CurrentUser, get_current_user
from src.core.common import (
    audit,
    envelope,
    get_project,
    get_project_entity,
    new_id,
    now,
    optimistic_patch,
)
from src.core.database import database
from src.domain.schemas import (
    AutomationScriptApproval,
    AutomationScriptGenerateInput,
    AutomationScriptPatch,
)
from src.services.design_assistance import ai_contract_metadata, request_design_assistance
from src.services.domain_policy import domain_policy

router = APIRouter(prefix="/kiem-thu", tags=["Kịch bản tự động hóa"])


def secret_policy():
    return domain_policy("secret_detection")


def validate_source(source):
    if re.search(secret_policy()["raw_assignment_pattern"], source, re.I):
        raise HTTPException(status_code=422, detail={"code": "RAW_SECRET_IN_SCRIPT"})
    return source


def generated_script(result):
    if result.get("status") != "SUCCESS" or result.get("degraded_mode"):
        raise HTTPException(503, detail={"code": "AI_PROVIDER_UNAVAILABLE", "retryable": True})
    suggestions = result.get("suggestions")
    if (
        not isinstance(suggestions, list)
        or len(suggestions) != 1
        or not isinstance(suggestions[0], dict)
    ):
        raise HTTPException(502, detail={"code": "AI_SCRIPT_INVALID"})
    source = suggestions[0].get("source")
    placeholders = suggestions[0].get("secret_placeholders", [])
    if (
        not isinstance(source, str)
        or not source.strip()
        or len(source) > 100000
        or source.lstrip().startswith("```")
    ):
        raise HTTPException(502, detail={"code": "AI_SCRIPT_INVALID"})
    if not isinstance(placeholders, list) or any(
        not isinstance(item, str)
        or not re.fullmatch(secret_policy()["placeholder_pattern"], item)
        for item in placeholders
    ):
        raise HTTPException(502, detail={"code": "AI_SCRIPT_PLACEHOLDERS_INVALID"})
    return validate_source(source), list(dict.fromkeys(placeholders))


def default_filename(framework, language, version):
    key = re.sub(r"[^A-Za-z0-9_-]+", "-", str(version.get("test_case_key") or "test-case"))
    suffix = {"typescript": "spec.ts", "javascript": "spec.js", "python": "py"}[language]
    return f"{key.lower()}.{framework}.{suffix}"


@router.get("/du-an/{project_id}/ban-nhap-kich-ban-tu-dong")
async def list_automation_script_drafts(
    project_id: str, user: CurrentUser = Depends(get_current_user)
):
    await get_project(project_id, user, "automation.script.export")
    items = (
        await database.value.automation_script_drafts.find({"project_id": project_id})
        .sort("updated_at", -1)
        .to_list(500)
    )
    return envelope(items)


@router.get("/ban-nhap-kich-ban-tu-dong/{draft_id}")
async def get_automation_script_draft(draft_id: str, user: CurrentUser = Depends(get_current_user)):
    value = await get_project_entity(
        "automation_script_drafts", draft_id, user, "automation.script.export"
    )
    return envelope(value, revision=value["revision"])


@router.post("/du-an/{project_id}/ai/ban-nhap-kich-ban-tu-dong", status_code=201)
async def generate_automation_script_draft(
    project_id: str,
    payload: AutomationScriptGenerateInput,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "ai.generate_automation_script")
    existing = await database.value.automation_script_drafts.find_one(
        {"project_id": project_id, "idempotency_key": payload.idempotency_key}
    )
    if existing:
        return envelope(existing, revision=existing["revision"])
    version = await database.value.test_case_versions.find_one(
        {"_id": payload.test_case_version_id, "project_id": project_id}
    )
    if not version:
        raise HTTPException(status_code=422, detail={"code": "INVALID_TEST_CASE_VERSION"})
    evidence = [
        {
            "artifact_type": "test_case_version",
            "artifact_id": version.get("test_case_id"),
            "artifact_version_id": version["_id"],
            "authority": "PROJECT_APPROVED_TEST",
            "text": " ".join(
                [str(version.get("title") or ""), str(version.get("plain_text_projection") or "")]
            )[:4000],
        }
    ]
    ai_result = await request_design_assistance(
        "automation_script_generation",
        project_id,
        json.dumps(
            {"framework": payload.framework, "language": payload.language},
            ensure_ascii=False,
        ),
        evidence
        + ([{"artifact_type": "user_context", "text": payload.context}] if payload.context else []),
    )
    source, placeholders = generated_script(ai_result)
    timestamp = now()
    ai_contract = ai_contract_metadata(ai_result)
    value = {
        "_id": new_id("AUTOSCR"),
        "project_id": project_id,
        "test_case_version_id": version["_id"],
        "test_case_id": version.get("test_case_id"),
        "test_case_key": version.get("test_case_key"),
        "framework": payload.framework,
        "language": payload.language,
        "filename": default_filename(payload.framework, payload.language, version),
        "source": source,
        "secret_placeholders": placeholders,
        "model_suggestions": ai_result.get("suggestions", []),
        **ai_contract,
        "ai_contract": ai_contract,
        "ai_status": ai_contract["status"],
        "generation_status": ai_result.get("status", "SUCCESS"),
        "status": "DRAFT",
        "candidate_only": True,
        "repository_write_performed": False,
        "human_confirmation_required": True,
        "idempotency_key": payload.idempotency_key,
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await database.value.automation_script_drafts.insert_one(value)
    except DuplicateKeyError:
        existing = await database.value.automation_script_drafts.find_one(
            {"project_id": project_id, "idempotency_key": payload.idempotency_key}
        )
        if existing:
            return envelope(existing, revision=existing["revision"])
        raise
    await audit(
        user.id,
        "automation_script_draft_generated",
        "AutomationScriptDraft",
        value["_id"],
        project_id,
        {"framework": payload.framework, "test_case_version_id": version["_id"]},
    )
    return envelope(
        value,
        revision=1,
        status=ai_result.get("status", "SUCCESS"),
        degraded_mode=ai_result.get("degraded_mode"),
    )


@router.patch("/ban-nhap-kich-ban-tu-dong/{draft_id}")
async def update_automation_script_draft(
    draft_id: str, payload: AutomationScriptPatch, user: CurrentUser = Depends(get_current_user)
):
    draft = await get_project_entity(
        "automation_script_drafts", draft_id, user, "automation.script.update"
    )
    if draft.get("status") != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "AUTOMATION_SCRIPT_NOT_DRAFT"})
    changes = payload.model_dump(exclude_unset=True)
    if payload.source is not None:
        changes["source"] = validate_source(payload.source)
    updated = await optimistic_patch(
        "automation_script_drafts",
        draft_id,
        draft["project_id"],
        payload.expected_revision,
        changes,
    )
    await audit(
        user.id,
        "automation_script_draft_updated",
        "AutomationScriptDraft",
        draft_id,
        draft["project_id"],
    )
    return envelope(updated, revision=updated["revision"])


@router.post("/ban-nhap-kich-ban-tu-dong/{draft_id}/phe-duyet")
async def approve_automation_script_draft(
    draft_id: str, payload: AutomationScriptApproval, user: CurrentUser = Depends(get_current_user)
):
    draft = await get_project_entity(
        "automation_script_drafts", draft_id, user, "automation.script.approve"
    )
    if draft.get("status") != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "AUTOMATION_SCRIPT_NOT_DRAFT"})
    validate_source(draft["source"])
    updated = await optimistic_patch(
        "automation_script_drafts",
        draft_id,
        draft["project_id"],
        payload.expected_revision,
        {
            "status": "APPROVED",
            "review_note": payload.review_note,
            "approved_by": user.id,
            "approved_at": now(),
            "human_confirmation_required": False,
        },
    )
    await audit(
        user.id,
        "automation_script_draft_approved",
        "AutomationScriptDraft",
        draft_id,
        draft["project_id"],
        {"review_note": payload.review_note},
    )
    return envelope(updated, revision=updated["revision"])


@router.get("/ban-nhap-kich-ban-tu-dong/{draft_id}/xuat")
async def export_automation_script_draft(
    draft_id: str, user: CurrentUser = Depends(get_current_user)
):
    draft = await get_project_entity(
        "automation_script_drafts", draft_id, user, "automation.script.export"
    )
    if draft.get("status") != "APPROVED":
        raise HTTPException(status_code=409, detail={"code": "AUTOMATION_SCRIPT_NOT_APPROVED"})
    source = validate_source(draft["source"])
    await audit(
        user.id,
        "automation_script_exported",
        "AutomationScriptDraft",
        draft_id,
        draft["project_id"],
        {"filename": draft["filename"]},
    )
    return Response(
        content=source,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{draft["filename"]}"'},
    )
