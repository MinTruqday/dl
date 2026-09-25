import hashlib
import json

from fastapi import HTTPException

from src.core.auth import CurrentUser
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, now
from src.core.rich_text import text_document
from src.domain.contracts import (
    APIArtifactArchive,
    APIArtifactConfirm,
    APIArtifactImpact,
    APIArtifactReview,
    ImportCreate,
    TestCaseDraftCreate,
)
from src.services.api_artifact_formats import (
    api_case_blueprints,
    model_metadata,
    operation_fingerprint,
    operation_identity,
    parse_openapi,
    parse_postman,
    public_api_import,
    sanitize_postman,
)
from src.repositories.api_artifact import api_artifact_repository
from src.services.domain_policy import domain_policy
from src.services.test_case_records import create_test_case_draft_record
from src.services.test_case_transfer import (
    confirm_test_import,
    export_test_cases,
    preview_test_import,
    recover_trace_links,
    upload_test_import,
)

API_POLICY = domain_policy("api_artifact")

__all__ = [
    "confirm_test_import",
    "export_test_cases",
    "preview_test_import",
    "recover_trace_links",
    "upload_test_import",
]


async def list_api_artifacts(
    project_id: str,
    status: str | None,
    user: CurrentUser,
):
    await get_project(project_id, user, API_POLICY["read_permission"])
    query = {"project_id": project_id}
    if status:
        query["status"] = status
    items = await api_artifact_repository.list_imports(
        query, API_POLICY["operation_limit"], ("created_at", -1)
    )
    return envelope([public_api_import(item) for item in items])


async def get_api_artifact(artifact_id: str, user: CurrentUser):
    artifact = await get_project_entity(API_POLICY["import_collection"], artifact_id, user, API_POLICY["read_permission"])
    operations = []
    if artifact.get("status") == API_POLICY["confirmed_status"]:
        operations = await api_artifact_repository.list_operations(
            {"project_id": artifact["project_id"], "import_id": artifact_id},
            API_POLICY["operation_limit"],
            ("path", 1),
        )
    return envelope(
        {**public_api_import(artifact, include_preview=True), "operations": operations},
        revision=artifact.get("revision", 1),
    )


async def import_api_artifact(
    project_id: str, payload: ImportCreate, user: CurrentUser
):
    await get_project(project_id, user, API_POLICY["import_permission"])
    if payload.format not in set(API_POLICY["supported_formats"]):
        raise HTTPException(status_code=422, detail={"code": API_POLICY["artifact_required_code"]})
    try:
        value = json.loads(payload.content) if isinstance(payload.content, str) else payload.content
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=422, detail={"code": API_POLICY["json_invalid_code"]}
        ) from error
    if not isinstance(value, dict):
        raise HTTPException(status_code=422, detail={"code": API_POLICY["object_required_code"]})
    operations = (
        parse_postman(value)
        if payload.format == API_POLICY["postman_format"]
        else parse_openapi(value)
    )
    if not operations:
        raise HTTPException(status_code=422, detail={"code": API_POLICY["no_operations_code"]})
    import_id = new_id(API_POLICY["import_id_prefix"])
    timestamp = now()
    serialized = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    job = {
        "_id": import_id,
        "project_id": project_id,
        "filename": payload.filename,
        "format": payload.format,
        "content_hash": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
        "preview": operations,
        "raw_content": sanitize_postman(value)
        if payload.format == API_POLICY["postman_format"]
        else None,
        "selected_indexes": list(range(len(operations))),
        "status": API_POLICY["preview_status"],
        "revision": API_POLICY["initial_revision"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    await api_artifact_repository.insert_import(job)
    await audit(
        user.id,
        API_POLICY["preview_created_event"],
        API_POLICY["import_entity"],
        import_id,
        project_id,
        {"operation_count": len(operations), "format": payload.format},
    )
    return envelope(public_api_import(job, include_preview=True), revision=API_POLICY["initial_revision"])


async def review_api_artifact(
    artifact_id: str, payload: APIArtifactReview, user: CurrentUser
):
    artifact = await get_project_entity(API_POLICY["import_collection"], artifact_id, user, API_POLICY["review_permission"])
    if artifact.get("status") not in set(API_POLICY["reviewable_statuses"]):
        raise HTTPException(status_code=409, detail={"code": API_POLICY["not_reviewable_code"]})
    preview = artifact.get("preview") or []
    selected = payload.selected_indexes or list(range(len(preview)))
    if len(set(selected)) != len(selected) or any(
        index < 0 or index >= len(preview) for index in selected
    ):
        raise HTTPException(status_code=422, detail={"code": API_POLICY["invalid_preview_index_code"]})
    timestamp = now()
    updated = await api_artifact_repository.transition_import(
        {
            "_id": artifact_id,
            "project_id": artifact["project_id"],
            "revision": payload.expected_revision,
            "status": {"$in": API_POLICY["reviewable_statuses"]},
        },
        {
            "selected_indexes": selected,
            "review_note": payload.review_note,
            "reviewed_by": user.id,
            "reviewed_at": timestamp,
            "updated_at": timestamp,
            "status": API_POLICY["reviewed_status"],
        },
        increment_revision=True,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": API_POLICY["revision_conflict_code"]})
    await audit(
        user.id,
        API_POLICY["reviewed_event"],
        API_POLICY["import_entity"],
        artifact_id,
        artifact["project_id"],
        {"selected_count": len(selected)},
    )
    return envelope(public_api_import(updated, include_preview=True), revision=updated["revision"])


async def confirm_api_artifact(
    artifact_id: str, payload: APIArtifactConfirm, user: CurrentUser
):
    artifact = await get_project_entity(API_POLICY["import_collection"], artifact_id, user, API_POLICY["confirm_permission"])
    if artifact.get("status") == API_POLICY["confirmed_status"]:
        if artifact.get("idempotency_key") != payload.idempotency_key:
            raise HTTPException(status_code=409, detail={"code": API_POLICY["idempotency_conflict_code"]})
        operations = await api_artifact_repository.list_operations(
            {"project_id": artifact["project_id"], "import_id": artifact_id},
            API_POLICY["operation_limit"],
            ("path", 1),
        )
        return envelope(
            {**public_api_import(artifact), "operations": operations}, revision=artifact["revision"]
        )
    if artifact.get("status") == API_POLICY["confirming_status"]:
        if artifact.get("idempotency_key") != payload.idempotency_key:
            raise HTTPException(status_code=409, detail={"code": API_POLICY["idempotency_conflict_code"]})
    elif artifact.get("status") != API_POLICY["reviewed_status"]:
        raise HTTPException(status_code=409, detail={"code": API_POLICY["review_required_code"]})
    if artifact.get("revision") != payload.expected_revision:
        raise HTTPException(
            status_code=409,
            detail={"code": API_POLICY["revision_conflict_code"], "current_revision": artifact.get("revision")},
        )
    if artifact.get("status") == API_POLICY["reviewed_status"]:
        claimed = await api_artifact_repository.transition_import(
            {
                "_id": artifact_id,
                "project_id": artifact["project_id"],
                "revision": payload.expected_revision,
                "status": API_POLICY["reviewed_status"],
            },
            {
                "status": API_POLICY["confirming_status"],
                "idempotency_key": payload.idempotency_key,
                "updated_at": now(),
            },
        )
        if not claimed:
            raise HTTPException(status_code=409, detail={"code": API_POLICY["revision_conflict_code"]})
        artifact = claimed
    selected = artifact.get("selected_indexes") or []
    preview = artifact.get("preview") or []
    timestamp = now()
    operations = [
        {
            "_id": f"{API_POLICY['operation_id_prefix']}-{hashlib.sha256(f'{artifact_id}:{index}'.encode()).hexdigest()[:32]}",
            "project_id": artifact["project_id"],
            "import_id": artifact_id,
            "source_index": index,
            **preview[index],
            "created_at": timestamp,
        }
        for index in selected
    ]
    for operation in operations:
        await api_artifact_repository.upsert_operation(operation)
    updated = await api_artifact_repository.transition_import(
        {
            "_id": artifact_id,
            "project_id": artifact["project_id"],
            "revision": payload.expected_revision,
            "status": API_POLICY["confirming_status"],
            "idempotency_key": payload.idempotency_key,
        },
        {
            "status": API_POLICY["confirmed_status"],
            "operation_ids": [operation["_id"] for operation in operations],
            "idempotency_key": payload.idempotency_key,
            "confirmed_by": user.id,
            "confirmed_at": timestamp,
            "updated_at": timestamp,
        },
        increment_revision=True,
    )
    if not updated:
        current = await api_artifact_repository.find_import(
            artifact_id, artifact["project_id"]
        )
        if not current or current.get("status") != API_POLICY["confirmed_status"]:
            raise HTTPException(status_code=409, detail={"code": API_POLICY["revision_conflict_code"]})
        updated = current
    persisted = await api_artifact_repository.list_operations(
        {"project_id": artifact["project_id"], "import_id": artifact_id},
        API_POLICY["operation_limit"],
        ("path", 1),
    )
    await audit(
        user.id,
        API_POLICY["confirmed_event"],
        API_POLICY["import_entity"],
        artifact_id,
        artifact["project_id"],
        {"operation_count": len(persisted)},
    )
    return envelope(
        {**public_api_import(updated), "operations": persisted}, revision=updated["revision"]
    )


async def list_api_operations(project_id: str, user: CurrentUser):
    await get_project(project_id, user, API_POLICY["read_permission"])
    return envelope(
        await api_artifact_repository.list_operations(
            {"project_id": project_id}, API_POLICY["operation_limit"], ("path", 1)
        )
    )


async def generate_api_tests(operation_id: str, user: CurrentUser):
    operation = await get_project_entity(
        API_POLICY["operation_collection"], operation_id, user, API_POLICY["generate_test_permission"]
    )
    cases = api_case_blueprints(operation)
    created = []
    for case in cases:
        draft = await create_test_case_draft_record(
            operation["project_id"],
            TestCaseDraftCreate(
                title=case["title"],
                type=API_POLICY["test_type"],
                priority=API_POLICY["high_level"]
                if case["category"] in set(API_POLICY["high_priority_categories"])
                else API_POLICY["medium_level"],
                risk=API_POLICY["high_level"]
                if case["category"] in set(API_POLICY["high_risk_categories"])
                else API_POLICY["medium_level"],
                preconditions_doc=text_document(
                    API_POLICY["operation_precondition_template"].format(
                        method=operation["method"], path=operation["path"]
                    )
                ),
                steps=[
                    {
                        "id": API_POLICY["step_id"],
                        "order": 1,
                        "action_doc": text_document(case["action"]),
                        "test_data": case["test_data"],
                        "expected_doc": text_document(case["expected"]),
                    }
                ],
                test_data=case["test_data"],
                expected_result_doc=text_document(case["expected"]),
                postconditions_doc=text_document(API_POLICY["secret_postcondition"]),
                tags=[*API_POLICY["generated_tags"], case["category"]],
                automation_status=API_POLICY["automation_status"],
                origin=API_POLICY["generated_origin"],
                source_evidence=[
                    {
                        "artifact_type": API_POLICY["operation_artifact_type"],
                        "artifact_version_id": operation_id,
                        "path": operation["path"],
                        "method": operation["method"],
                    }
                ],
            ),
            user,
        )
        created.append(draft)
    await audit(
        user.id,
        API_POLICY["tests_generated_event"],
        API_POLICY["operation_entity"],
        operation_id,
        operation["project_id"],
        {"count": len(created)},
    )
    return envelope(
        {"items": created, "model": model_metadata(API_POLICY["test_generation_model"]), "evidence": operation}
    )


async def build_api_artifact_diff(project_id, from_artifact_id, to_artifact_id):
    artifacts = await api_artifact_repository.list_imports(
        {
            "_id": {"$in": [from_artifact_id, to_artifact_id]},
            "project_id": project_id,
            "status": API_POLICY["confirmed_status"],
        },
        2,
    )
    if len(artifacts) != 2:
        raise HTTPException(status_code=422, detail={"code": API_POLICY["version_invalid_code"]})
    operations = await api_artifact_repository.list_operations(
        {"project_id": project_id, "import_id": {"$in": [from_artifact_id, to_artifact_id]}},
        API_POLICY["diff_operation_limit"],
    )
    by_import = {from_artifact_id: {}, to_artifact_id: {}}
    for operation in operations:
        by_import[operation["import_id"]][operation_identity(operation)] = operation
    before = by_import[from_artifact_id]
    after = by_import[to_artifact_id]
    before_keys = set(before)
    after_keys = set(after)
    return {
        "from_artifact_id": from_artifact_id,
        "to_artifact_id": to_artifact_id,
        "added": [after[identity] for identity in sorted(after_keys - before_keys)],
        "removed": [before[identity] for identity in sorted(before_keys - after_keys)],
        "changed": [
            {"identity": identity, "before": before[identity], "after": after[identity]}
            for identity in sorted(before_keys & after_keys)
            if operation_fingerprint(before[identity]) != operation_fingerprint(after[identity])
        ],
    }


async def diff_api_artifacts(
    project_id: str,
    from_artifact_id: str,
    to_artifact_id: str,
    user: CurrentUser,
):
    await get_project(project_id, user, API_POLICY["diff_read_permission"])
    return envelope(await build_api_artifact_diff(project_id, from_artifact_id, to_artifact_id))


async def analyze_api_artifact_impact(
    project_id: str, payload: APIArtifactImpact, user: CurrentUser
):
    await get_project(project_id, user, API_POLICY["impact_permission"])
    existing = await api_artifact_repository.find_impact(
        project_id,
        API_POLICY["impact_source_type"],
        payload.from_artifact_id,
        payload.to_artifact_id,
    )
    if existing:
        return envelope(existing, revision=existing.get("revision", 1))
    difference = await build_api_artifact_diff(
        project_id, payload.from_artifact_id, payload.to_artifact_id
    )
    affected_operations = {item["_id"] for item in difference["removed"]} | {
        item["before"]["_id"] for item in difference["changed"]
    }
    current_cases = await api_artifact_repository.list_test_cases(
        project_id, API_POLICY["current_test_statuses"], API_POLICY["test_case_limit"]
    )
    versions = await api_artifact_repository.list_test_case_versions(
        project_id,
        [item["current_version_id"] for item in current_cases if item.get("current_version_id")],
        API_POLICY["test_case_limit"],
    )
    affected = []
    for version in versions:
        evidence_ids = {
            evidence.get("artifact_version_id")
            for evidence in version.get("source_evidence", [])
            if evidence.get("artifact_type") == API_POLICY["operation_artifact_type"]
        }
        matched = sorted(affected_operations & evidence_ids)
        if not matched:
            continue
        affected.append(
            {
                "test_case_id": version.get("test_case_id"),
                "test_case_version_id": version["_id"],
                "classification": API_POLICY["needs_update_classification"],
                "confidence": API_POLICY["initial_revision"],
                "reasons": [API_POLICY["changed_source_reason"]],
                "evidence": [{"api_operation_ids": matched}],
            }
        )
    new_test_requirements = [
        {
            "classification": API_POLICY["new_test_classification"],
            "reason": API_POLICY["new_operation_reason"],
            "evidence": {"api_operation_id": operation["_id"]},
        }
        for operation in difference["added"]
    ]
    analysis = {
        "_id": new_id(API_POLICY["impact_id_prefix"]),
        "project_id": project_id,
        "source_type": API_POLICY["impact_source_type"],
        "from_artifact_id": payload.from_artifact_id,
        "to_artifact_id": payload.to_artifact_id,
        "difference": difference,
        "affected_test_cases": affected,
        "new_test_requirements": new_test_requirements,
        "status": API_POLICY["impact_status"],
        "revision": API_POLICY["initial_revision"],
        "mode": API_POLICY["deterministic_mode"],
        "created_by": user.id,
        "created_at": now(),
    }
    await api_artifact_repository.insert_impact(analysis)
    await audit(
        user.id,
        API_POLICY["impact_created_event"],
        API_POLICY["impact_entity"],
        analysis["_id"],
        project_id,
        {"affected_count": len(affected), "new_test_requirement_count": len(new_test_requirements)},
    )
    return envelope(analysis, revision=API_POLICY["initial_revision"])


async def archive_api_artifact(
    artifact_id: str, payload: APIArtifactArchive, user: CurrentUser
):
    artifact = await get_project_entity(API_POLICY["import_collection"], artifact_id, user, API_POLICY["archive_permission"])
    if artifact.get("status") == API_POLICY["archived_status"]:
        return envelope(public_api_import(artifact), revision=artifact.get("revision", 1))
    timestamp = now()
    updated = await api_artifact_repository.transition_import(
        {
            "_id": artifact_id,
            "project_id": artifact["project_id"],
            "revision": payload.expected_revision,
            "status": {"$ne": API_POLICY["archived_status"]},
        },
        {
            "status": API_POLICY["archived_status"],
            "archive_reason": payload.reason,
            "archived_by": user.id,
            "archived_at": timestamp,
            "updated_at": timestamp,
        },
        increment_revision=True,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": API_POLICY["revision_conflict_code"]})
    await audit(
        user.id,
        API_POLICY["archived_event"],
        API_POLICY["import_entity"],
        artifact_id,
        artifact["project_id"],
        {"reason": payload.reason},
    )
    return envelope(public_api_import(updated), revision=updated["revision"])
