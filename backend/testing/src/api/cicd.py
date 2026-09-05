import hashlib
import hmac

from fastapi import APIRouter, Depends, Header, HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.api.automation_execution import public_execution, redact
from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, now
from src.core.configuration import settings
from src.core.database import database
from src.domain.schemas import (
    CiCdBindingCreate,
    CiCdBindingPatch,
    CiCdResultInput,
    CiCdRetryInput,
    CiCdTriggerInput,
)


router = APIRouter(prefix="/kiem-thu", tags=["Tích hợp triển khai liên tục"])
internal_router = APIRouter(
    prefix="/noi-bo/kiem-thu/tich-hop-trien-khai-lien-tuc",
    tags=["Tích hợp triển khai liên tục nội bộ"],
)


def verify_signature(value, signature):
    expected = hmac.new(settings.SECRET_KEY.encode(), value.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=403, detail={"code": "INVALID_JOB_CONTEXT_SIGNATURE"})


def public_binding(value):
    result = dict(value)
    result["pipeline_reference"] = "Đã cấu hình"
    return result


@router.get("/du-an/{project_id}/tich-hop-trien-khai-lien-tuc")
async def list_cicd_state(project_id: str, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "cicd.read")
    bindings = await database.value.cicd_bindings.find({"project_id": project_id}).sort("updated_at", -1).to_list(500)
    runs = await database.value.pipeline_runs.find({"project_id": project_id}).sort("created_at", -1).to_list(1000)
    reconciliations = await database.value.cicd_reconciliation_jobs.find({"project_id": project_id}).sort("created_at", -1).to_list(1000)
    return envelope({"bindings": [public_binding(item) for item in bindings], "runs": redact(runs), "reconciliations": reconciliations})


@router.post("/du-an/{project_id}/tich-hop-trien-khai-lien-tuc", status_code=201)
async def create_cicd_binding(project_id: str, payload: CiCdBindingCreate, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "cicd.manage")
    connector = await database.value.project_connectors.find_one({"_id": payload.connector_id, "project_id": project_id, "status": "BOUND", "enabled": True})
    if not connector:
        raise HTTPException(status_code=422, detail={"code": "ACTIVE_CONNECTOR_REQUIRED"})
    if payload.postman_artifact_id:
        artifact = await database.value.api_imports.find_one({"_id": payload.postman_artifact_id, "project_id": project_id, "format": "postman", "status": "CONFIRMED"})
        if not artifact:
            raise HTTPException(status_code=422, detail={"code": "CONFIRMED_POSTMAN_COLLECTION_REQUIRED"})
    timestamp = now()
    value = {"_id": new_id("CIBIND"), "project_id": project_id, **payload.model_dump(), "enabled": True, "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    try:
        await database.value.cicd_bindings.insert_one(value)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail={"code": "PIPELINE_ALREADY_BOUND"})
    await audit(user.id, "cicd_binding_created", "CiCdBinding", value["_id"], project_id, {"connector_id": payload.connector_id})
    return envelope(public_binding(value), revision=1)


@router.patch("/du-an/{project_id}/tich-hop-trien-khai-lien-tuc/{binding_id}")
async def update_cicd_binding(project_id: str, binding_id: str, payload: CiCdBindingPatch, user: CurrentUser = Depends(get_current_user)):
    binding = await get_project_entity("cicd_bindings", binding_id, user, "cicd.manage")
    if binding["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    updated = await database.value.cicd_bindings.find_one_and_update({"_id": binding_id, "project_id": project_id, "revision": payload.expected_revision}, {"$set": {**changes, "updated_at": now()}, "$inc": {"revision": 1}}, return_document=ReturnDocument.AFTER)
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "cicd_binding_updated", "CiCdBinding", binding_id, project_id)
    return envelope(public_binding(updated), revision=updated["revision"])


@internal_router.post("/kich-hoat", include_in_schema=False, status_code=202)
async def trigger_cicd_run(payload: CiCdTriggerInput, x_internal_token: str = Header(default="")):
    if not hmac.compare_digest(x_internal_token, settings.SECRET_KEY):
        raise HTTPException(status_code=403, detail={"code": "INVALID_INTERNAL_TOKEN"})
    verify_signature(f"{payload.project_id}:{payload.binding_id}:{payload.external_run_id}:{payload.idempotency_key}", payload.context_signature)
    existing = await database.value.pipeline_runs.find_one({"project_id": payload.project_id, "idempotency_key": payload.idempotency_key})
    if existing:
        return envelope(existing, operation_id=existing["_id"])
    binding = await database.value.cicd_bindings.find_one({"_id": payload.binding_id, "project_id": payload.project_id, "enabled": True})
    if not binding:
        raise HTTPException(status_code=422, detail={"code": "ACTIVE_PIPELINE_BINDING_REQUIRED"})
    timestamp = now()
    automation = {"_id": new_id("AUTOEX"), "project_id": payload.project_id, "name": f"CI {binding['name']} {payload.external_run_id}", "runner": "external_ci", "postman_artifact_id": binding.get("postman_artifact_id"), "release_id": binding.get("release_id"), "test_case_version_ids": binding.get("test_case_version_ids", []), "status": "RUNNING", "summary": {}, "results": [], "logs": [], "artifact_refs": [], "idempotency_key": f"ci:{payload.idempotency_key}", "revision": 1, "created_by": "service:cicd", "created_at": timestamp, "updated_at": timestamp}
    run = {"_id": new_id("PIPERUN"), "project_id": payload.project_id, "binding_id": payload.binding_id, "automation_execution_id": automation["_id"], "external_run_id": payload.external_run_id, "commit_reference": payload.commit_reference, "status": "RUNNING", "attempt": 1, "idempotency_key": payload.idempotency_key, "revision": 1, "created_at": timestamp, "updated_at": timestamp}
    try:
        await database.value.automation_executions.insert_one(automation)
        await database.value.pipeline_runs.insert_one(run)
    except DuplicateKeyError:
        existing = await database.value.pipeline_runs.find_one({"project_id": payload.project_id, "idempotency_key": payload.idempotency_key})
        if existing:
            return envelope(existing, operation_id=existing["_id"])
        raise
    await audit("service:cicd", "cicd_run_triggered", "PipelineRun", run["_id"], payload.project_id, {"external_run_id": payload.external_run_id})
    return envelope(run, operation_id=run["_id"])


@internal_router.post("/ket-qua", include_in_schema=False)
async def ingest_cicd_result(payload: CiCdResultInput, x_internal_token: str = Header(default="")):
    if not hmac.compare_digest(x_internal_token, settings.SECRET_KEY):
        raise HTTPException(status_code=403, detail={"code": "INVALID_INTERNAL_TOKEN"})
    verify_signature(f"{payload.project_id}:{payload.pipeline_run_id}:{payload.status}", payload.context_signature)
    run = await database.value.pipeline_runs.find_one({"_id": payload.pipeline_run_id, "project_id": payload.project_id})
    if not run:
        raise HTTPException(status_code=404, detail={"code": "PIPELINE_RUN_NOT_FOUND"})
    if run.get("status") in {"COMPLETED", "FAILED", "CANCELLED"}:
        return envelope(run, revision=run["revision"])
    timestamp = now()
    updated = await database.value.pipeline_runs.find_one_and_update({"_id": payload.pipeline_run_id, "project_id": payload.project_id, "status": "RUNNING"}, {"$set": {"status": payload.status, "summary": redact(payload.summary), "logs": redact(payload.logs), "completed_at": timestamp, "updated_at": timestamp}, "$inc": {"revision": 1}}, return_document=ReturnDocument.AFTER)
    await database.value.automation_executions.update_one({"_id": run["automation_execution_id"], "project_id": payload.project_id, "status": "RUNNING"}, {"$set": {"status": payload.status, "summary": redact(payload.summary), "results": redact(payload.results), "logs": redact(payload.logs), "completed_at": timestamp, "updated_at": timestamp}, "$inc": {"revision": 1}})
    await audit("service:cicd", "cicd_result_ingested", "PipelineRun", run["_id"], payload.project_id, {"status": payload.status})
    return envelope(updated, revision=updated["revision"])


@router.post("/du-an/{project_id}/tich-hop-trien-khai-lien-tuc/lan-chay/{run_id}/thu-lai", status_code=202)
async def retry_cicd_run(project_id: str, run_id: str, payload: CiCdRetryInput, user: CurrentUser = Depends(get_current_user)):
    run = await get_project_entity("pipeline_runs", run_id, user, "cicd.retry")
    if run["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    existing = await database.value.cicd_reconciliation_jobs.find_one({"project_id": project_id, "idempotency_key": payload.idempotency_key})
    if existing:
        return envelope(existing, operation_id=existing["_id"])
    if run.get("status") != "FAILED" or run.get("revision") != payload.expected_revision:
        raise HTTPException(status_code=409, detail={"code": "PIPELINE_RUN_NOT_RETRYABLE"})
    timestamp = now()
    value = {"_id": new_id("CIREC"), "project_id": project_id, "pipeline_run_id": run_id, "binding_id": run["binding_id"], "status": "QUEUED", "reason": payload.reason, "idempotency_key": payload.idempotency_key, "requested_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    try:
        await database.value.cicd_reconciliation_jobs.insert_one(value)
    except DuplicateKeyError:
        existing = await database.value.cicd_reconciliation_jobs.find_one({"project_id": project_id, "idempotency_key": payload.idempotency_key})
        if existing:
            return envelope(existing, operation_id=existing["_id"])
        raise
    await audit(user.id, "cicd_reconciliation_queued", "PipelineRun", run_id, project_id, {"operation_id": value["_id"], "reason": payload.reason})
    return envelope(value, operation_id=value["_id"])
