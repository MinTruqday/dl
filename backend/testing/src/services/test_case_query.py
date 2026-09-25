from fastapi import HTTPException

from src.core.common import audit, get_project, get_project_entity, now, page_payload, sort_spec
from src.domain.contracts import TestCaseDraftCreate
from src.repositories.test_design import test_design_repository
from src.services.domain_policy import domain_policy
from src.services.test_case_records import create_test_case_draft_record

QUERY_POLICY = domain_policy("test_case_query")


async def list_test_case_records(
    project_id,
    user,
    q="",
    key="",
    title="",
    status="",
    priority="",
    test_type="",
    technique="",
    stale_status="",
    automation_status="",
    requirement_id="",
    suite_id="",
    latest_result="",
    tag="",
    owner="",
    page=1,
    page_size=50,
    sort="-updated_at",
):
    await get_project(project_id, user, QUERY_POLICY["read_permission"])
    tests = await test_design_repository.list_cases(
        project_id, status, QUERY_POLICY["case_limit"]
    )
    version_ids = [item["current_version_id"] for item in tests if item.get("current_version_id")]
    versions = await test_design_repository.list_case_versions_by_ids(
        project_id, version_ids, QUERY_POLICY["case_limit"]
    )
    by_id = {item["_id"]: item for item in versions}
    items = [{**item, "current_version": by_id.get(item.get("current_version_id"))} for item in tests]
    traces = await test_design_repository.list_confirmed_case_traces(
        project_id,
        version_ids,
        QUERY_POLICY["confirmed_trace_status"],
        QUERY_POLICY["trace_limit"],
    )
    trace_counts = {}
    for trace in traces:
        trace_counts[trace["target_id"]] = trace_counts.get(trace["target_id"], 0) + 1
    results = await test_design_repository.list_case_results(
        project_id, version_ids, QUERY_POLICY["result_limit"]
    )
    latest_results = {}
    for result in results:
        latest_results.setdefault(result["test_case_version_id"], result.get("status"))
    suite_version_ids = set()
    if suite_id:
        suite = await test_design_repository.find_suite(suite_id, project_id)
        if not suite:
            raise HTTPException(status_code=422, detail={"code": QUERY_POLICY["invalid_suite_code"]})
        suite_version_ids = set(suite.get("test_case_version_ids", []))
    requirement_version_ids = set()
    if requirement_id:
        requirement_version_ids = {
            item["_id"]
            for item in await test_design_repository.list_requirement_version_ids(
                project_id, requirement_id, QUERY_POLICY["requirement_version_limit"]
            )
        }
        requirement_version_ids.add(requirement_id)
    for item in items:
        version = item.get("current_version") or {}
        version_id = item.get("current_version_id")
        item["trace_count"] = trace_counts.get(version_id, 0)
        item["latest_result"] = latest_results.get(version_id)
        item["stale_status"] = version.get("stale_status") or (
            QUERY_POLICY["stale_status"]
            if item.get("status") == QUERY_POLICY["needs_update_status"]
            else QUERY_POLICY["fresh_status"]
        )
        item["owner_id"] = version.get("owner_id")
        item["tags"] = sorted(set(item.get("tags", [])) | set(version.get("tags", [])))
    terms = [value.strip().lower() for value in (q, key, title) if value.strip()]
    if terms:
        items = [item for item in items if matches_test_case(item, terms)]
    field_filters = {
        "priority": priority,
        "type": test_type,
        "automation_status": automation_status,
        "owner_id": owner,
    }
    for field, value in field_filters.items():
        if value:
            items = [
                item
                for item in items
                if (item.get("current_version") or {}).get(field, item.get(field)) == value
            ]
    if technique:
        items = [item for item in items if technique in (item.get("current_version") or {}).get("techniques", [])]
    if tag:
        items = [item for item in items if tag in item.get("tags", [])]
    if stale_status:
        items = [item for item in items if item.get("stale_status") == stale_status]
    if latest_result:
        items = [item for item in items if item.get("latest_result") == latest_result]
    if requirement_id:
        items = [
            item
            for item in items
            if requirement_version_ids
            & set((item.get("current_version") or {}).get("requirement_version_ids", []))
        ]
    if suite_id:
        items = [item for item in items if item.get("current_version_id") in suite_version_ids]
    sort_field, direction = sort_spec(
        sort,
        {
            "test_case_key",
            "status",
            "updated_at",
            "created_at",
            "title",
            "priority",
            "stale_status",
            "latest_result",
        },
    )
    items.sort(
        key=lambda item: str(
            (item.get("current_version") or {}).get(sort_field, item.get(sort_field, "")) or ""
        ).lower(),
        reverse=direction < 0,
    )
    total = len(items)
    start = (page - 1) * page_size
    return page_payload(items[start : start + page_size], page, page_size, total)


def matches_test_case(item, terms):
    version = item.get("current_version") or {}
    searchable = f"{item.get('test_case_key', '')} {version.get('title', '')}".lower()
    return all(value in searchable for value in terms)


async def list_test_case_drafts(project_id, limit, user):
    await get_project(project_id, user, QUERY_POLICY["read_permission"])
    return await test_design_repository.list_case_drafts(project_id, limit)


async def get_test_case_record(test_case_id, user):
    test_case = await get_project_entity(QUERY_POLICY["case_collection"], test_case_id, user, QUERY_POLICY["read_permission"])
    version = await test_design_repository.find_case_version(
        test_case.get("current_version_id"), test_case["project_id"]
    )
    return {**test_case, "current_version": version}


async def clone_test_case_record(test_case_id, payload, user):
    test_case = await get_project_entity(QUERY_POLICY["case_collection"], test_case_id, user, QUERY_POLICY["clone_permission"])
    if test_case.get("current_version_id") != payload.expected_current_version_id:
        raise HTTPException(
            status_code=409,
            detail={"code": QUERY_POLICY["revision_conflict_code"], "current_version_id": test_case.get("current_version_id")},
        )
    version = await test_design_repository.find_case_version(
        payload.expected_current_version_id, test_case["project_id"]
    )
    if not version or version.get("test_case_id") != test_case_id:
        raise HTTPException(status_code=422, detail={"code": QUERY_POLICY["version_not_found_code"]})
    source_evidence = [
        *version.get("source_evidence", []),
        {
            "artifact_type": QUERY_POLICY["version_artifact_type"],
            "artifact_id": test_case_id,
            "artifact_version_id": version["_id"],
            "relation": QUERY_POLICY["clone_relation"],
        },
    ]
    result = await create_test_case_draft_record(
        test_case["project_id"],
        TestCaseDraftCreate(
            title=payload.title or f"{version['title']}{QUERY_POLICY['clone_title_suffix']}",
            type=version["type"],
            priority=version["priority"],
            risk=version["risk"],
            objective_doc=version.get("objective_doc", {"type": "doc", "content": []}),
            preconditions_doc=version["preconditions_doc"],
            steps=version["steps"],
            test_data=version["test_data"],
            expected_result_doc=version["expected_result_doc"],
            postconditions_doc=version["postconditions_doc"],
            tags=version.get("tags", []),
            techniques=version.get("techniques", []),
            automation_status=version.get(
                "automation_status", QUERY_POLICY["manual_automation_status"]
            ),
            attachments=version.get("attachments", []),
            data_set_version_ids=version.get("data_set_version_ids", []),
            requirement_version_ids=version.get("requirement_version_ids", []),
            acceptance_criterion_ids=version.get("acceptance_criterion_ids", []),
            scenario_id=version.get("scenario_id"),
            origin=QUERY_POLICY["clone_origin"],
            source_evidence=source_evidence,
        ),
        user,
    )
    await audit(
        user.id,
        QUERY_POLICY["cloned_event"],
        QUERY_POLICY["draft_entity"],
        result["_id"],
        test_case["project_id"],
        {"source_test_case_id": test_case_id, "source_version_id": version["_id"]},
    )
    return result


async def list_test_case_versions(test_case_id, user):
    await get_project_entity(QUERY_POLICY["case_collection"], test_case_id, user, QUERY_POLICY["version_read_permission"])
    return await test_design_repository.list_versions_for_case(
        test_case_id, QUERY_POLICY["version_limit"]
    )


async def create_test_case_version_draft_record(test_case_id, payload, user):
    test_case = await get_project_entity(QUERY_POLICY["case_collection"], test_case_id, user, QUERY_POLICY["version_create_permission"])
    expected_version_id = str(payload.get("expected_current_version_id") or "")
    if expected_version_id != test_case.get("current_version_id"):
        raise HTTPException(
            status_code=409,
            detail={"code": QUERY_POLICY["revision_conflict_code"], "current_version_id": test_case.get("current_version_id")},
        )
    reason = str(payload.get("change_reason") or "").strip()
    if len(reason) < 2:
        raise HTTPException(status_code=422, detail={"code": QUERY_POLICY["change_reason_required_code"]})
    version = await test_design_repository.find_case_version(
        expected_version_id, test_case["project_id"]
    )
    if not version or version.get("test_case_id") != test_case_id:
        raise HTTPException(status_code=404, detail={"code": QUERY_POLICY["entity_not_found_code"]})
    result = await create_test_case_draft_record(
        test_case["project_id"],
        TestCaseDraftCreate(
            test_case_key=test_case["test_case_key"],
            title=str(payload.get("title") or version["title"]),
            type=version["type"],
            priority=version["priority"],
            risk=version["risk"],
            objective_doc=version.get("objective_doc", {"type": "doc", "content": []}),
            preconditions_doc=version["preconditions_doc"],
            steps=version["steps"],
            test_data=version["test_data"],
            expected_result_doc=version["expected_result_doc"],
            postconditions_doc=version["postconditions_doc"],
            tags=version.get("tags", []),
            techniques=version.get("techniques", []),
            automation_status=version.get(
                "automation_status", QUERY_POLICY["manual_automation_status"]
            ),
            attachments=version.get("attachments", []),
            data_set_version_ids=version.get("data_set_version_ids", []),
            requirement_version_ids=version.get("requirement_version_ids", []),
            acceptance_criterion_ids=version.get("acceptance_criterion_ids", []),
            scenario_id=version.get("scenario_id"),
            origin=QUERY_POLICY["manual_origin"],
            source_evidence=[
                *version.get("source_evidence", []),
                {
                    "artifact_type": QUERY_POLICY["version_artifact_type"],
                    "artifact_id": test_case_id,
                    "artifact_version_id": version["_id"],
                    "relation": QUERY_POLICY["new_version_relation"],
                },
            ],
        ),
        user,
    )
    await test_design_repository.update_case_draft_metadata(
        result["_id"], {"change_reason": reason, "parent_version_id": version["_id"]}
    )
    result["change_reason"] = reason
    result["parent_version_id"] = version["_id"]
    return result


async def diff_test_case_version_records(test_case_id, from_version, to_version, user):
    test_case = await get_project_entity(QUERY_POLICY["case_collection"], test_case_id, user, QUERY_POLICY["version_read_permission"])
    versions = await test_design_repository.list_selected_case_versions(
        test_case["project_id"], test_case_id, [from_version, to_version]
    )
    by_id = {item["_id"]: item for item in versions}
    if from_version not in by_id or to_version not in by_id:
        raise HTTPException(status_code=404, detail={"code": QUERY_POLICY["entity_not_found_code"]})
    before = by_id[from_version]
    after = by_id[to_version]
    fields = [
        "title", "type", "priority", "risk", "objective_doc", "preconditions_doc", "steps",
        "test_data", "expected_result_doc", "postconditions_doc", "tags", "techniques",
        "automation_status", "requirement_version_ids", "acceptance_criterion_ids",
    ]
    return {
        "test_case_id": test_case_id,
        "from_version_id": from_version,
        "to_version_id": to_version,
        "changes": [
            {"field": field, "before": before.get(field), "after": after.get(field)}
            for field in fields
            if before.get(field) != after.get(field)
        ],
    }


async def set_test_case_obsolete(test_case_id, payload, user):
    test_case = await get_project_entity(QUERY_POLICY["case_collection"], test_case_id, user, QUERY_POLICY["archive_permission"])
    if test_case.get("status") == QUERY_POLICY["obsolete_status"]:
        return test_case
    if test_case.get("status") not in {
        QUERY_POLICY["active_status"],
        QUERY_POLICY["needs_update_status"],
    }:
        raise HTTPException(status_code=409, detail={"code": QUERY_POLICY["invalid_transition_code"]})
    if payload.get("expected_current_version_id") != test_case.get("current_version_id"):
        raise HTTPException(status_code=409, detail={"code": QUERY_POLICY["revision_conflict_code"], "current_version_id": test_case.get("current_version_id")})
    reason = str(payload.get("reason") or "").strip()
    if len(reason) < 2:
        raise HTTPException(status_code=422, detail={"code": QUERY_POLICY["obsolete_reason_required_code"]})
    timestamp = now()
    updated = await test_design_repository.set_case_lifecycle_status(
        test_case_id,
        test_case["project_id"],
        QUERY_POLICY["obsolete_status"],
        {
            "obsolete_reason": reason,
            "obsolete_by": user.id,
            "obsolete_at": timestamp,
            "updated_at": timestamp,
        },
    )
    await audit(user.id, QUERY_POLICY["obsolete_event"], QUERY_POLICY["case_entity"], test_case_id, test_case["project_id"], {"reason": reason})
    return updated


async def restore_test_case_record(test_case_id, payload, user):
    test_case = await get_project_entity(QUERY_POLICY["case_collection"], test_case_id, user, QUERY_POLICY["restore_permission"])
    if test_case.get("status") != QUERY_POLICY["obsolete_status"]:
        return test_case
    if payload.get("expected_current_version_id") != test_case.get("current_version_id"):
        raise HTTPException(status_code=409, detail={"code": QUERY_POLICY["revision_conflict_code"]})
    reason = str(payload.get("reason") or "").strip()
    if len(reason) < 2:
        raise HTTPException(status_code=422, detail={"code": QUERY_POLICY["restore_reason_required_code"]})
    timestamp = now()
    updated = await test_design_repository.set_case_lifecycle_status(
        test_case_id,
        test_case["project_id"],
        QUERY_POLICY["active_status"],
        {
            "restore_reason": reason,
            "restored_by": user.id,
            "restored_at": timestamp,
            "updated_at": timestamp,
        },
    )
    await audit(user.id, QUERY_POLICY["restored_event"], QUERY_POLICY["case_entity"], test_case_id, test_case["project_id"], {"reason": reason})
    return updated
