import hashlib
import hmac
import json
import re

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, now
from src.core.configuration import settings
from src.core.database import database
from src.domain.schemas import (
    AutomationExecutionAction,
    AutomationExecutionCreate,
    AutomationExecutionResultInput,
)


router = APIRouter(prefix="/kiem-thu", tags=["Thực thi tự động"])
internal_router = APIRouter(
    prefix="/noi-bo/kiem-thu/thuc-thi-tu-dong", tags=["Thực thi tự động nội bộ"]
)
SECRET_PATTERN = re.compile(r"(?i)(token|secret|password|authorization|cookie|api[-_]?key)")


def redact(value):
    if isinstance(value, dict):
        return {
            key: "Đã ẩn" if SECRET_PATTERN.search(str(key)) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def public_execution(value, evidence=False):
    excluded = {"runner_payload", "context_signature"}
    if not evidence:
        excluded |= {"results", "logs", "artifact_refs"}
    return redact({key: item for key, item in value.items() if key not in excluded})


@router.get("/du-an/{project_id}/thuc-thi-tu-dong")
async def list_automation_executions(
    project_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "automation.read")
    items = await database.value.automation_executions.find(
        {"project_id": project_id}
    ).sort("created_at", -1).to_list(1000)
    return envelope([public_execution(item) for item in items])


@router.get("/thuc-thi-tu-dong/{execution_id}")
async def get_automation_execution(
    execution_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    value = await get_project_entity(
        "automation_executions", execution_id, user, "automation.read"
    )
    return envelope(public_execution(value), revision=value["revision"])


@router.post("/du-an/{project_id}/thuc-thi-tu-dong", status_code=201)
async def create_automation_execution(
    project_id: str,
    payload: AutomationExecutionCreate,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "automation.create")
    existing = await database.value.automation_executions.find_one(
        {"project_id": project_id, "idempotency_key": payload.idempotency_key}
    )
    if existing:
        return envelope(public_execution(existing), revision=existing["revision"])
    artifact = await database.value.api_imports.find_one(
        {
            "_id": payload.postman_artifact_id,
            "project_id": project_id,
            "format": "postman",
            "status": "CONFIRMED",
        }
    )
    if not artifact or not artifact.get("raw_content"):
        raise HTTPException(
            status_code=422, detail={"code": "CONFIRMED_POSTMAN_COLLECTION_REQUIRED"}
        )
    environment = None
    if payload.environment_id:
        environment = await database.value.test_environments.find_one(
            {
                "_id": payload.environment_id,
                "project_id": project_id,
                "status": {"$ne": "ARCHIVED"},
            }
        )
        if not environment:
            raise HTTPException(status_code=422, detail={"code": "INVALID_ENVIRONMENT"})
    timestamp = now()
    value = {
        "_id": new_id("AUTOEX"),
        "project_id": project_id,
        "name": payload.name,
        "runner": "newman",
        "postman_artifact_id": artifact["_id"],
        "environment_id": payload.environment_id,
        "environment_snapshot": {
            "name": environment.get("name"),
            "variable_names": sorted((environment.get("variables") or {}).keys()),
            "secret_reference_names": sorted(
                (environment.get("secret_references") or {}).keys()
            ),
        }
        if environment
        else None,
        "runner_payload": {"collection": artifact["raw_content"]},
        "status": "CREATED",
        "summary": {},
        "results": [],
        "logs": [],
        "artifact_refs": [],
        "idempotency_key": payload.idempotency_key,
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await database.value.automation_executions.insert_one(value)
    except DuplicateKeyError:
        existing = await database.value.automation_executions.find_one(
            {"project_id": project_id, "idempotency_key": payload.idempotency_key}
        )
        if existing:
            return envelope(public_execution(existing), revision=existing["revision"])
        raise
    await audit(
        user.id,
        "automation_execution_created",
        "AutomationExecution",
        value["_id"],
        project_id,
        {"postman_artifact_id": artifact["_id"], "runner": "newman"},
    )
    return envelope(public_execution(value), revision=1)


@router.post("/thuc-thi-tu-dong/{execution_id}/bat-dau", status_code=202)
async def start_automation_execution(
    execution_id: str,
    payload: AutomationExecutionAction,
    user: CurrentUser = Depends(get_current_user),
):
    execution = await get_project_entity(
        "automation_executions", execution_id, user, "automation.execute"
    )
    if execution.get("status") == "QUEUED" and execution.get("start_idempotency_key") == payload.idempotency_key:
        return envelope(public_execution(execution), operation_id=execution.get("operation_id"))
    if execution.get("status") != "CREATED" or execution.get("revision") != payload.expected_revision:
        raise HTTPException(status_code=409, detail={"code": "AUTOMATION_STATE_CONFLICT"})
    request = {
        "event": "automation.newman.requested",
        "project_id": execution["project_id"],
        "artifact_version_id": execution_id,
        "model_version": "newman-v1",
        "requester_id": user.id,
        "requester_email": user.email,
        "payload": {
            "execution_id": execution_id,
            "collection": execution["runner_payload"]["collection"],
        },
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{settings.WORKER_URL}/xu-ly-nen/noi-bo/kiem-thu/tac-vu",
                headers={"X-Internal-Token": settings.SECRET_KEY},
                json=request,
            )
            response.raise_for_status()
            operation_id = response.json()["job_id"]
    except httpx.HTTPError as error:
        raise HTTPException(status_code=503, detail={"code": "WORKER_UNAVAILABLE"}) from error
    updated = await database.value.automation_executions.find_one_and_update(
        {"_id": execution_id, "revision": payload.expected_revision, "status": "CREATED"},
        {
            "$set": {
                "status": "QUEUED",
                "operation_id": operation_id,
                "start_idempotency_key": payload.idempotency_key,
                "queued_at": now(),
                "updated_at": now(),
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "AUTOMATION_STATE_CONFLICT"})
    await audit(user.id, "automation_execution_queued", "AutomationExecution", execution_id, execution["project_id"], {"operation_id": operation_id})
    return envelope(public_execution(updated), operation_id=operation_id)


@router.post("/thuc-thi-tu-dong/{execution_id}/huy")
async def cancel_automation_execution(
    execution_id: str,
    payload: AutomationExecutionAction,
    user: CurrentUser = Depends(get_current_user),
):
    execution = await get_project_entity(
        "automation_executions", execution_id, user, "automation.execute"
    )
    if execution.get("status") == "CANCELLED":
        return envelope(public_execution(execution), revision=execution["revision"])
    if execution.get("status") != "QUEUED" or execution.get("revision") != payload.expected_revision:
        raise HTTPException(status_code=409, detail={"code": "AUTOMATION_NOT_CANCELLABLE"})
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{settings.WORKER_URL}/xu-ly-nen/noi-bo/tac-vu/{execution['operation_id']}/huy",
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
            response.raise_for_status()
    except httpx.HTTPError as error:
        raise HTTPException(status_code=503, detail={"code": "WORKER_UNAVAILABLE"}) from error
    updated = await database.value.automation_executions.find_one_and_update(
        {"_id": execution_id, "revision": payload.expected_revision, "status": "QUEUED"},
        {"$set": {"status": "CANCELLED", "cancelled_by": user.id, "cancelled_at": now(), "updated_at": now()}, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    await audit(user.id, "automation_execution_cancelled", "AutomationExecution", execution_id, execution["project_id"])
    return envelope(public_execution(updated), revision=updated["revision"])


@router.get("/thuc-thi-tu-dong/{execution_id}/bang-chung")
async def get_automation_evidence(
    execution_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    value = await get_project_entity(
        "automation_executions", execution_id, user, "automation.read"
    )
    return envelope(public_execution(value, evidence=True), revision=value["revision"])


@internal_router.post("/ket-qua", include_in_schema=False)
async def ingest_automation_result(
    payload: AutomationExecutionResultInput,
    x_internal_token: str = Header(default=""),
):
    if not hmac.compare_digest(x_internal_token, settings.SECRET_KEY):
        raise HTTPException(status_code=403, detail={"code": "INVALID_INTERNAL_TOKEN"})
    signature_value = f"{payload.execution_id}:{payload.operation_id}:{payload.status}"
    expected = hmac.new(
        settings.SECRET_KEY.encode(), signature_value.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, payload.context_signature):
        raise HTTPException(status_code=403, detail={"code": "INVALID_JOB_CONTEXT_SIGNATURE"})
    execution = await database.value.automation_executions.find_one(
        {"_id": payload.execution_id, "operation_id": payload.operation_id}
    )
    if not execution:
        raise HTTPException(status_code=404, detail={"code": "AUTOMATION_EXECUTION_NOT_FOUND"})
    if execution.get("status") in {"COMPLETED", "FAILED", "CANCELLED"}:
        return envelope(public_execution(execution, evidence=True), revision=execution["revision"])
    updated = await database.value.automation_executions.find_one_and_update(
        {"_id": payload.execution_id, "operation_id": payload.operation_id, "status": {"$in": ["QUEUED", "RUNNING"]}},
        {"$set": {"status": payload.status, "summary": redact(payload.summary), "results": redact(payload.results), "logs": redact(payload.logs), "artifact_refs": payload.artifact_refs, "completed_at": now(), "updated_at": now()}, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "AUTOMATION_STATE_CONFLICT"})
    await audit("service:worker", "automation_result_ingested", "AutomationExecution", payload.execution_id, updated["project_id"], {"operation_id": payload.operation_id, "status": payload.status})
    return envelope(public_execution(updated, evidence=True), revision=updated["revision"])
