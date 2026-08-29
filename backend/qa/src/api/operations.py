import httpx
import re
from fastapi import APIRouter, Depends, HTTPException, Query

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope, now
from src.core.configuration import settings
from src.core.database import database


router = APIRouter(prefix="/api/qa", tags=["QA Operations"])


async def require_system_admin(user: CurrentUser):
    if not user.is_system_admin:
        raise HTTPException(status_code=403, detail={"code": "PLATFORM_ADMIN_REQUIRED"})


def attachment_size(value):
    if isinstance(value, dict):
        total = 0
        for key, item in value.items():
            if key in {"size", "size_bytes", "bytes", "byte_size"} and isinstance(item, (int, float)):
                total += int(item)
            elif isinstance(item, (dict, list)):
                total += attachment_size(item)
        return total
    if isinstance(value, list):
        return sum(attachment_size(item) for item in value)
    return 0


async def project_storage_usage():
    projects = await database.value.projects.find({}, {"_id": 1, "key": 1, "name": 1}).to_list(10000)
    collections = [
        ("requirement_documents", "raw_source"),
        ("test_case_drafts", "attachments"),
        ("test_case_versions", "attachments"),
        ("test_results", "attachments"),
        ("defects", "attachments"),
    ]
    usage = []
    for project in projects:
        project_id = project["_id"]
        total = 0
        file_count = 0
        for collection_name, field in collections:
            rows = await getattr(database.value, collection_name).find({"project_id": project_id}, {field: 1}).to_list(10000)
            for row in rows:
                value = row.get(field)
                total += attachment_size(value)
                if isinstance(value, list):
                    file_count += len(value)
                elif isinstance(value, dict) and value:
                    file_count += 1
        usage.append({"project_id": project_id, "project_key": project.get("key"), "project_name": project.get("name"), "bytes": total, "files": file_count})
    usage.sort(key=lambda item: item["bytes"], reverse=True)
    return usage


@router.get("/operations")
async def operations(
    limit: int = Query(default=100, ge=1, le=500),
    audit_q: str = Query(default="", max_length=200),
    audit_event: str = Query(default="", max_length=120),
    audit_project_id: str = Query(default="", max_length=128),
    user: CurrentUser = Depends(get_current_user),
):
    await require_system_admin(user)
    failed_ingestion = await database.value.import_jobs.find(
        {"status": {"$in": ["FAILED", "PARSE_FAILED"]}}
    ).sort("created_at", -1).to_list(limit)
    failed_impact = await database.value.impact_analyses.find(
        {"status": {"$in": ["FAILED", "DEGRADED"]}}
    ).sort("updated_at", -1).to_list(limit)
    worker_failures = await database.value.worker_events.find(
        {"status": "FAILED"}
    ).sort("completed_at", -1).to_list(limit)
    indexing_backlog = await database.value.requirement_versions.count_documents(
        {"index_status": {"$in": ["PENDING", "FAILED"]}}
    ) + await database.value.test_case_versions.count_documents(
        {"index_status": {"$in": ["PENDING", "FAILED"]}}
    )
    ai_models = {
        "impact_analysis": "agentic-hybrid-v1",
        "maintenance_proposal": "maintenance-agent-v1",
        "regression": "risk-score-v1",
    }
    audit_filter = {}
    if audit_event:
        audit_filter["action"] = audit_event
    if audit_project_id:
        audit_filter["project_id"] = audit_project_id
    if audit_q:
        pattern = re.escape(audit_q)
        audit_filter["$or"] = [
            {"action": {"$regex": pattern, "$options": "i"}},
            {"entity_type": {"$regex": pattern, "$options": "i"}},
            {"entity_id": {"$regex": pattern, "$options": "i"}},
            {"actor_id": {"$regex": pattern, "$options": "i"}},
        ]
    audit_events = await database.value.audit_events.find(audit_filter).sort("created_at", -1).to_list(limit)
    for event in audit_events:
        if hasattr(event.get("created_at"), "isoformat"):
            event["created_at"] = event["created_at"].isoformat()
    return envelope(
        {
            "generated_at": now(),
            "failed_ingestion_jobs": failed_ingestion,
            "failed_impact_jobs": failed_impact,
            "worker_failures": worker_failures,
            "storage_usage": await project_storage_usage(),
            "audit_events": audit_events,
            "rag_indexing_backlog": indexing_backlog,
            "ai_models": ai_models,
            "ai_request_metrics": {
                "impact_analyses": await database.value.impact_analyses.count_documents({}),
                "proposals": await database.value.maintenance_proposals.count_documents({}),
            },
        }
    )


@router.post("/operations/jobs/{job_id}/retry", status_code=202)
async def retry_failed_job(job_id: str, user: CurrentUser = Depends(get_current_user)):
    await require_system_admin(user)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{settings.WORKER_URL}/worker/internal/jobs/{job_id}/retry",
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
            response.raise_for_status()
            return envelope(response.json())
    except httpx.HTTPStatusError as error:
        code = "WORKER_RETRY_FAILED"
        if error.response.status_code == 404:
            code = "JOB_NOT_FOUND"
        elif error.response.status_code == 409:
            code = "JOB_RETRY_NOT_ALLOWED"
        raise HTTPException(status_code=error.response.status_code, detail={"code": code}) from error
    except httpx.HTTPError as error:
        raise HTTPException(status_code=503, detail={"code": "WORKER_UNAVAILABLE"}) from error
