import hmac

from fastapi import APIRouter, Header, HTTPException

from src.api.api_artifacts import recover_trace_links
from src.api.changes import analyze_impact, create_change_set
from src.api.test_design import find_duplicates, generate_test_cases
from src.core.auth import CurrentUser
from src.core.common import envelope, now
from src.core.configuration import settings
from src.core.database import database
from src.domain.schemas import GenerateInput, RequirementCompareInput
from src.services.project_rag import index_artifact


router = APIRouter(prefix="/api/qa/internal/jobs", tags=["QA Internal Jobs"])


@router.post("/{event}")
async def process_job(
    event: str,
    body: dict,
    x_internal_token: str = Header(default=""),
    x_requester_id: str = Header(default=""),
    x_requester_email: str = Header(default=""),
):
    if not hmac.compare_digest(x_internal_token, settings.SECRET_KEY):
        raise HTTPException(status_code=403, detail={"code": "INVALID_INTERNAL_TOKEN"})
    allowed = {"document.parse.requested", "requirement.extract.requested", "requirement.semantic_diff.requested", "test.generate.requested", "duplicate.scan.requested", "impact.analysis.requested", "rag.index.requested"}
    if event not in allowed:
        raise HTTPException(status_code=422, detail={"code": "UNSUPPORTED_JOB_EVENT"})
    user = CurrentUser(
        _id=x_requester_id,
        email=x_requester_email or "worker@internal",
        system_role="USER",
    )
    payload = body.get("payload") if isinstance(body.get("payload"), dict) else {}
    result = await execute(event, body, payload, user)
    completed = not (isinstance(result, dict) and result.get("indexed") is False)
    record = {"_id": body.get("job_id"), "project_id": body.get("project_id"), "artifact_version_id": body.get("artifact_version_id"), "event": event, "model_version": body.get("model_version"), "status": "COMPLETED" if completed else "FAILED", "error_code": None if completed else "RAG_INDEX_FAILED", "retryable": not completed, "state_after_failure": "INDEX_FAILED" if not completed else None, "result": result, "completed_at": now()}
    await database.value.worker_events.update_one({"_id": record["_id"]}, {"$set": record}, upsert=True)
    return envelope(record)


async def execute(event, body, payload, user):
    if event == "impact.analysis.requested":
        return (await analyze_impact(payload.get("change_set_id") or body.get("artifact_version_id"), user))["data"]
    if event == "duplicate.scan.requested":
        return (await find_duplicates(body["project_id"], user))["data"]
    if event == "test.generate.requested":
        request = GenerateInput(**{key: value for key, value in payload.items() if key in {"categories", "count_per_category", "instruction"}})
        return (await generate_test_cases(body["artifact_version_id"], request, user))["data"]
    if event == "requirement.semantic_diff.requested":
        request = RequirementCompareInput(from_version_id=payload["from_version_id"], to_version_id=payload["to_version_id"])
        return (await create_change_set(payload["requirement_id"], request, user))["data"]
    if event == "rag.index.requested":
        return await reindex(body["project_id"], body["artifact_version_id"])
    if event == "requirement.extract.requested":
        return {"status": "READY_FOR_PREVIEW", "import_job_id": payload.get("import_job_id")}
    if event == "document.parse.requested":
        return {"status": "READY_FOR_EXTRACTION", "document_id": payload.get("document_id")}
    return {"status": "COMPLETED"}


async def reindex(project_id, version_id):
    artifact = await database.value.requirement_versions.find_one({"_id": version_id, "project_id": project_id})
    artifact_type = "requirement_version"
    logical_key = "requirement_id"
    if not artifact:
        artifact = await database.value.test_case_versions.find_one({"_id": version_id, "project_id": project_id})
        artifact_type = "test_case_version"
        logical_key = "test_case_id"
    if not artifact:
        raise HTTPException(status_code=404, detail={"code": "ARTIFACT_VERSION_NOT_FOUND"})
    indexed = await index_artifact(project_id, artifact_type, artifact[logical_key], artifact["_id"], artifact.get("title", ""), artifact.get("plain_text_projection", ""), artifact.get("status", "ACTIVE"), "baseline" if artifact.get("status") == "BASELINED" else "approved", artifact.get("version"))
    return {"indexed": indexed, "artifact_version_id": version_id}
