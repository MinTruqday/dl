from fastapi import HTTPException

from src.core.auth import CurrentUser
from src.core.common import get_project, now
from src.repositories.analysis import analysis_repository
from src.domain.contracts import GenerateInput, RequirementCompareInput
from src.services.change_set import create_change_set_record
from src.services.domain_policy import domain_policy
from src.services.impact_analysis import create_impact_analysis_record
from src.services.job_policy import ALLOWED_JOB_EVENTS, JOB_EVENT_PERMISSIONS
from src.clients.project_knowledge import index_artifact
from src.services.test_case_assistance import (
    find_duplicate_test_case_records,
    generate_test_case_draft_records,
)


async def process_delegated_job(
    event: str,
    body: dict,
    requester_id: str,
    requester_email: str,
):
    policy = domain_policy("delegated_jobs")
    if event not in ALLOWED_JOB_EVENTS:
        raise HTTPException(
            status_code=422, detail={"code": policy["unsupported_event_code"]}
        )
    if not requester_id:
        raise HTTPException(status_code=422, detail={"code": policy["identity_required_code"]})
    project_id = str(body.get("project_id") or "")
    if not project_id:
        raise HTTPException(status_code=422, detail={"code": policy["identity_required_code"]})
    user = CurrentUser(
        _id=requester_id,
        email=requester_email or policy["internal_worker_email"],
        system_role=policy["user_role"],
    )
    for permission in JOB_EVENT_PERMISSIONS[event]:
        await get_project(project_id, user, permission)
    payload = body.get("payload") if isinstance(body.get("payload"), dict) else {}
    result = await execute_job(event, body, payload, user)
    completed = not (isinstance(result, dict) and result.get("indexed") is False)
    record = {
        "_id": body.get("job_id"),
        "project_id": project_id,
        "artifact_version_id": body.get("artifact_version_id"),
        "event": event,
        "model_version": body.get("model_version"),
        "status": policy["completed_status"] if completed else policy["failed_status"],
        "error_code": None if completed else policy["index_failed_code"],
        "retryable": not completed,
        "state_after_failure": policy["index_failed_state"] if not completed else None,
        "result": result,
        "completed_at": now(),
    }
    await analysis_repository.upsert_worker_event(record["_id"], record)
    return record


async def execute_job(event: str, body: dict, payload: dict, user: CurrentUser):
    policy = domain_policy("delegated_jobs")
    if event == policy["impact_analysis_event"]:
        return await create_impact_analysis_record(
            payload.get("change_set_id") or body.get("artifact_version_id"), None, user
        )
    if event == policy["duplicate_scan_event"]:
        return await find_duplicate_test_case_records(body["project_id"], user)
    if event == policy["test_generate_event"]:
        request = GenerateInput(
            **{
                key: value
                for key, value in payload.items()
                if key in {"categories", "count_per_category", "instruction"}
            }
        )
        return await generate_test_case_draft_records(body["artifact_version_id"], request, user)
    if event == policy["semantic_diff_event"]:
        request = RequirementCompareInput(
            from_version_id=payload["from_version_id"], to_version_id=payload["to_version_id"]
        )
        return await create_change_set_record(payload["requirement_id"], request, user)
    if event == policy["knowledge_index_event"]:
        return await reindex_artifact(body["project_id"], body["artifact_version_id"])
    if event == policy["requirement_extract_event"]:
        return {
            "status": policy["ready_for_preview_status"],
            "import_job_id": payload.get("import_job_id"),
        }
    if event == policy["document_parse_event"]:
        return {
            "status": policy["ready_for_extraction_status"],
            "document_id": payload.get("document_id"),
        }
    return {"status": policy["completed_status"]}


async def reindex_artifact(project_id: str, version_id: str):
    policy = domain_policy("delegated_jobs")
    artifact = await analysis_repository.find_requirement_version(project_id, version_id)
    artifact_type = policy["requirement_artifact_type"]
    logical_key = policy["requirement_logical_key"]
    if not artifact:
        artifact = await analysis_repository.find_test_case_version(project_id, version_id)
        artifact_type = policy["test_case_artifact_type"]
        logical_key = policy["test_case_logical_key"]
    if not artifact:
        raise HTTPException(status_code=404, detail={"code": policy["artifact_not_found_code"]})
    indexed = await index_artifact(
        project_id,
        artifact_type,
        artifact[logical_key],
        artifact["_id"],
        artifact.get("title", ""),
        artifact.get("plain_text_projection", ""),
        artifact.get("status", policy["active_artifact_status"]),
        policy["approved_source_authority"],
        artifact.get("version"),
    )
    return {"indexed": indexed, "artifact_version_id": version_id}
