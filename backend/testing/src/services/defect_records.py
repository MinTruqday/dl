import csv
import io
import re

from fastapi import HTTPException

from src.core.common import (
    audit,
    get_project,
    get_project_entity,
    get_project_role,
    new_id,
    next_key,
    now,
    page_payload,
    sort_spec,
    visible_defect,
)
from src.repositories import defect_repository
from src.services.domain_policy import domain_policy
from src.services.execution_context import resolve_execution_context
from src.clients.project_knowledge import index_artifact


async def create_defect_record(project_id, payload, user):
    policy = domain_policy("defect")
    if project_id != payload.project_id:
        raise HTTPException(status_code=422, detail={"code": policy["project_mismatch_code"]})
    await get_project(project_id, user, "defect.create")
    context = await resolve_execution_context(
        project_id,
        user,
        release_id=payload.release_id,
        build_id=payload.build_id,
        environment_id=payload.environment_id,
        release=payload.release,
        build=payload.build,
        environment=payload.environment,
    )
    if payload.linked_test_result_id:
        result = await defect_repository.find_test_result(
            payload.linked_test_result_id, project_id
        )
        if not result or result["status"] != policy["failed_result_status"]:
            raise HTTPException(status_code=422, detail={"code": policy["failed_result_required_code"]})
    timestamp = now()
    defect = {
        "_id": new_id(policy["id_prefix"]),
        **payload.model_dump(),
        **context,
        "defect_key": payload.defect_key
        or await next_key(project_id, policy["counter_name"], policy["key_prefix"]),
        "status": policy["initial_status"],
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    await defect_repository.insert_defect(defect)
    await index_artifact(
        project_id,
        "defect",
        defect["_id"],
        defect["_id"],
        defect["title"],
        " ".join(
            [defect["title"], str(defect.get("environment", "")), str(defect.get("build", ""))]
        ),
        defect["status"],
        policy["project_reference_authority"],
        1,
        linked_test_result_id=defect.get("linked_test_result_id"),
        linked_requirement_version_ids=defect.get("linked_requirement_version_ids", []),
    )
    await audit(user.id, "defect_created", "Defect", defect["_id"], project_id)
    return defect


async def list_defect_records(
    project_id,
    user,
    q="",
    key="",
    title="",
    status="",
    severity="",
    priority="",
    assignee="",
    release="",
    release_id="",
    environment="",
    environment_id="",
    build="",
    build_id="",
    requirement_id="",
    test_case_id="",
    page=1,
    page_size=50,
    sort="-updated_at",
):
    policy = domain_policy("defect")
    await get_project(project_id, user, "defect.read")
    query = {"project_id": project_id}
    search_terms = [value.strip() for value in (q, key, title) if value.strip()]
    if search_terms:
        query["$and"] = [
            {
                "$or": [
                    {"defect_key": {"$regex": re.escape(value), "$options": "i"}},
                    {"title": {"$regex": re.escape(value), "$options": "i"}},
                ]
            }
            for value in search_terms
        ]
    if status:
        query["status"] = status
    for field, value in {
        "severity": severity,
        "priority": priority,
        "assignee": assignee,
        "release": release,
        "release_id": release_id,
        "environment": environment,
        "environment_id": environment_id,
        "build": build,
        "build_id": build_id,
        "linked_test_case_version_id": test_case_id,
    }.items():
        if value:
            query[field] = value
    if requirement_id:
        version_ids = await defect_repository.list_requirement_version_ids(
            project_id, requirement_id, policy["requirement_lookup_limit"]
        )
        version_ids.append(requirement_id)
        query["linked_requirement_version_ids"] = {"$in": version_ids}
    if test_case_id:
        version_ids = await defect_repository.list_test_case_version_ids(
            project_id, test_case_id, policy["case_lookup_limit"]
        )
        version_ids.append(test_case_id)
        query["linked_test_case_version_id"] = {"$in": version_ids}
    sort_field, direction = sort_spec(
        sort,
        set(policy["sort_fields"]),
    )
    total = await defect_repository.count_defects(query)
    items = await defect_repository.list_defects(
        query, sort_field, direction, (page - 1) * page_size, page_size
    )
    role = await get_project_role(project_id, user.id)
    return page_payload([visible_defect(item, role) for item in items], page, page_size, total)


async def build_defect_export(project_id, user):
    policy = domain_policy("defect")
    await get_project(project_id, user, "report.export")
    defects = await defect_repository.list_project_defects(project_id, policy["export_limit"])
    fields = policy["export_fields"]
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for defect in defects:
        writer.writerow({field: defect.get(field) for field in fields})
    return stream.getvalue()


async def get_defect_record(defect_id, project_id, user):
    policy = domain_policy("defect")
    defect = await get_project_entity("defects", defect_id, user, "defect.read")
    if project_id is not None and defect["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": policy["project_mismatch_code"]})
    role = await get_project_role(defect["project_id"], user.id)
    trace_links = await defect_repository.list_trace_links(
        defect["project_id"],
        defect_id,
        policy["artifact_type"],
        policy["related_limit"],
    )
    comments = (
        []
        if role == policy["viewer_role"]
        else await defect_repository.list_comments(
            defect["project_id"],
            defect_id,
            policy["artifact_type"],
            policy["related_limit"],
        )
    )
    attachments = (
        []
        if role == policy["viewer_role"]
        else await defect_repository.list_attachments(
            defect["project_id"],
            defect_id,
            policy["artifact_type"],
            policy["active_attachment_status"],
            policy["related_limit"],
        )
    )
    return {
        **visible_defect(defect, role),
        "trace_links": trace_links,
        "comments": comments,
        "attachments": attachments,
    }
