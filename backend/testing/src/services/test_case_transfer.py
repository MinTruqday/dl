import csv
import io

from fastapi import HTTPException, UploadFile

from src.core.auth import CurrentUser
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, now
from src.core.configuration import settings
from src.repositories.test_design import test_design_repository
from src.core.rich_text import text_document
from src.domain.contracts import ImportConfirm, ImportCreate, TestCaseDraftCreate
from src.services.api_artifact_formats import create_xlsx, lexical_similarity, model_metadata, terms
from src.services.domain_policy import domain_policy
from src.services.requirement_import import extract_xlsx_csv
from src.services.test_case_records import create_test_case_draft_record


async def recover_trace_links(project_id: str, user: CurrentUser):
    policy = domain_policy("test_case_transfer")
    await get_project(project_id, user, "trace.recover")
    requirements = await test_design_repository.list_requirement_versions(
        {"project_id": project_id, "status": policy["baselined_status"]},
        policy["requirement_limit"],
    )
    tests = await test_design_repository.list_case_versions(
        {"project_id": project_id, "status": policy["active_status"]},
        policy["case_limit"],
    )
    existing = await test_design_repository.list_trace_links(
        {"project_id": project_id, "status": {"$in": policy["existing_trace_statuses"]}},
        policy["trace_limit"],
    )
    pairs = {(item["source_id"], item["target_id"]) for item in existing}
    recovery_policy = domain_policy("trace_recovery")
    suggestions = []
    for test in tests:
        ranked = sorted(
            (
                (
                    lexical_similarity(
                        req.get("plain_text_projection", ""), test.get("plain_text_projection", "")
                    ),
                    req,
                )
                for req in requirements
            ),
            key=lambda item: item[0],
            reverse=True,
        )
        for score, requirement in ranked[: recovery_policy["maximum_candidates_per_test"]]:
            if (
                score < recovery_policy["minimum_score"]
                or (requirement["_id"], test["_id"]) in pairs
            ):
                continue
            link = {
                "_id": new_id(policy["trace_id_prefix"]),
                "project_id": project_id,
                "source_type": policy["trace_source_type"],
                "source_id": requirement["_id"],
                "target_type": policy["trace_target_type"],
                "target_id": test["_id"],
                "link_type": policy["trace_link_type"],
                "confidence": score,
                "origin": policy["trace_origin"],
                "status": policy["suggested_status"],
                "evidence": [
                    {
                        "matched_terms": sorted(
                            terms(requirement.get("plain_text_projection", ""))
                            & terms(test.get("plain_text_projection", ""))
                        )
                    }
                ],
                "created_by": user.id,
                "created_at": now(),
                "updated_at": now(),
            }
            suggestions.append(link)
    await test_design_repository.insert_trace_links(suggestions)
    await audit(
        user.id,
        "trace_recovery_completed",
        "Project",
        project_id,
        project_id,
        {"suggestion_count": len(suggestions)},
    )
    return envelope({"items": suggestions, "model": model_metadata("trace_recovery")})


async def preview_test_import(
    project_id: str, payload: ImportCreate, user: CurrentUser
):
    policy = domain_policy("test_case_transfer")
    await get_project(project_id, user, "testcase.import")
    if payload.format not in policy["supported_formats"]:
        raise HTTPException(status_code=422, detail={"code": policy["unsupported_format_code"]})
    content = str(payload.content)
    rows = list(csv.DictReader(io.StringIO(content)))
    preview = [
        {
            "title": row.get("title") or f"{policy['default_title_prefix']}{index + 1}",
            "type": row.get("type") or policy["default_type"],
            "priority": row.get("priority") or policy["default_priority"],
            "risk": row.get("risk") or policy["default_risk"],
            "precondition": row.get("precondition") or policy["default_precondition"],
            "action": row.get("action") or row.get("steps") or policy["default_action"],
            "expected": row.get("expected")
            or row.get("expected_result")
            or policy["default_expected"],
            "tags": [item.strip() for item in (row.get("tags") or "").split(",") if item.strip()],
        }
        for index, row in enumerate(rows[: policy["preview_limit"]])
    ]
    job = {
        "_id": new_id(policy["import_id_prefix"]),
        "project_id": project_id,
        "filename": payload.filename,
        "format": payload.format,
        "preview": preview,
        "status": policy["preview_status"],
        "created_by": user.id,
        "created_at": now(),
    }
    await test_design_repository.insert_import(job)
    return envelope(job)


async def upload_test_import(
    project_id: str,
    format: str,
    file: UploadFile,
    user: CurrentUser,
):
    policy = domain_policy("test_case_transfer")
    if format not in policy["supported_formats"]:
        raise HTTPException(status_code=422, detail={"code": policy["unsupported_format_code"]})
    data = await file.read()
    if len(data) > settings.MAX_API_ARTIFACT_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail={"code": policy["import_too_large_code"]})
    content = (
        extract_xlsx_csv(data)
        if format == policy["spreadsheet_format"]
        else data.decode(policy["csv_encoding"])
    )
    return await preview_test_import(
        project_id,
        ImportCreate(
            filename=file.filename or f"{policy['upload_filename_prefix']}.{format}",
            format=format,
            content=content,
        ),
        user,
    )


async def confirm_test_import(
    job_id: str, payload: ImportConfirm, user: CurrentUser
):
    policy = domain_policy("test_case_transfer")
    job = await get_project_entity("test_imports", job_id, user, "testcase.import")
    if job["status"] == policy["confirmed_status"]:
        return envelope(job)
    selected = payload.selected_indexes or list(range(len(job["preview"])))
    created = []
    for index in selected:
        if index < 0 or index >= len(job["preview"]):
            raise HTTPException(status_code=422, detail={"code": policy["invalid_preview_index_code"]})
        item = job["preview"][index]
        draft = await create_test_case_draft_record(
            job["project_id"],
            TestCaseDraftCreate(
                title=item["title"],
                type=item["type"],
                priority=item["priority"],
                risk=item["risk"],
                preconditions_doc=text_document(item["precondition"]),
                steps=[
                    {
                        "id": policy["default_step_id"],
                        "order": 1,
                        "action_doc": text_document(item["action"]),
                        "test_data": {},
                        "expected_doc": text_document(item["expected"]),
                    }
                ],
                test_data={},
                expected_result_doc=text_document(item["expected"]),
                postconditions_doc=text_document(policy["default_postcondition"]),
                tags=item["tags"],
                origin=policy["import_origin"],
            ),
            user,
        )
        created.append(draft)
    await test_design_repository.confirm_import(
        job_id,
        {
            "status": policy["confirmed_status"],
            "created_draft_ids": [item["_id"] for item in created],
            "confirmed_at": now(),
        },
    )
    return envelope({"job_id": job_id, "drafts": created})


async def export_test_cases(
    project_id: str,
    format: str,
    user: CurrentUser,
):
    policy = domain_policy("test_case_transfer")
    await get_project(project_id, user, "testcase.export")
    versions = await test_design_repository.list_case_versions(
        {"project_id": project_id},
        policy["export_limit"],
        policy["export_sort_field"],
        1,
    )
    fields = policy["export_fields"]
    rows = [[item.get(field) for field in fields] for item in versions]
    if format == policy["spreadsheet_format"]:
        content = create_xlsx([fields, *rows])
        return {
            "content": content,
            "media_type": policy["spreadsheet_media_type"],
            "filename": f"{policy['export_filename_prefix']}{project_id}.xlsx",
        }
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for item in versions:
        writer.writerow({field: item.get(field) for field in fields})
    return {
        "content": stream.getvalue(),
        "media_type": policy["csv_media_type"],
        "filename": f"{policy['export_filename_prefix']}{project_id}.csv",
    }
