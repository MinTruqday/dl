import csv
import io

from fastapi import HTTPException, UploadFile

from src.core.auth import CurrentUser
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, now
from src.repositories.test_design import test_design_repository
from src.core.rich_text import text_document
from src.schemas.contracts.design import TestCaseDraftCreate
from src.schemas.contracts.requirements import (
    ImportConfirm,
    ImportCreate,
)
from src.modules.integrations.services.api_artifact_formats import create_xlsx, lexical_similarity, model_metadata, terms
from src.modules.requirements.services.requirement_import import extract_xlsx_csv
from src.modules.design.services.test_case_records import create_test_case_draft_record


async def recover_trace_links(project_id: str, user: CurrentUser):
    
    await get_project(project_id, user, "trace.recover")
    requirements = await test_design_repository.list_requirement_versions(
        {"project_id": project_id, "status": 'BASELINED'},
        5000,
    )
    tests = await test_design_repository.list_case_versions(
        {"project_id": project_id, "status": 'ACTIVE'},
        10000,
    )
    existing = await test_design_repository.list_trace_links(
        {"project_id": project_id, "status": {"$in": ['CONFIRMED', 'SUGGESTED']}},
        50000,
    )
    pairs = {(item["source_id"], item["target_id"]) for item in existing}
    
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
        for score, requirement in ranked[: 3]:
            if (
                score < 0.18
                or (requirement["_id"], test["_id"]) in pairs
            ):
                continue
            link = {
                "_id": new_id('TL'),
                "project_id": project_id,
                "source_type": 'requirement_version',
                "source_id": requirement["_id"],
                "target_type": 'test_case_version',
                "target_id": test["_id"],
                "link_type": 'verifies',
                "confidence": score,
                "origin": 'trace_recovery',
                "status": 'SUGGESTED',
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
    
    await get_project(project_id, user, "testcase.import")
    if payload.format not in ['csv', 'xlsx']:
        raise HTTPException(status_code=422, detail={"code": 'TEST_IMPORT_FORMAT_UNSUPPORTED'})
    content = str(payload.content)
    rows = list(csv.DictReader(io.StringIO(content)))
    preview = [
        {
            "title": row.get("title") or f"{'Test Case dòng '}{index + 1}",
            "type": row.get("type") or 'custom',
            "priority": row.get("priority") or 'medium',
            "risk": row.get("risk") or 'medium',
            "precondition": row.get("precondition") or 'Hệ thống sẵn sàng',
            "action": row.get("action") or row.get("steps") or 'Thực hiện thao tác',
            "expected": row.get("expected")
            or row.get("expected_result")
            or 'Kết quả đúng theo đặc tả',
            "tags": [item.strip() for item in (row.get("tags") or "").split(",") if item.strip()],
        }
        for index, row in enumerate(rows[: 5000])
    ]
    job = {
        "_id": new_id('TIMP'),
        "project_id": project_id,
        "filename": payload.filename,
        "format": payload.format,
        "preview": preview,
        "status": 'PREVIEW_READY',
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
    
    if format not in ['csv', 'xlsx']:
        raise HTTPException(status_code=422, detail={"code": 'TEST_IMPORT_FORMAT_UNSUPPORTED'})
    data = await file.read()
    if len(data) > 20971520:
        raise HTTPException(status_code=413, detail={"code": 'IMPORT_TOO_LARGE'})
    content = (
        extract_xlsx_csv(data)
        if format == 'xlsx'
        else data.decode('utf-8-sig')
    )
    return await preview_test_import(
        project_id,
        ImportCreate(
            filename=file.filename or f"{'test-cases'}.{format}",
            format=format,
            content=content,
        ),
        user,
    )


async def confirm_test_import(
    job_id: str, payload: ImportConfirm, user: CurrentUser
):
    
    job = await get_project_entity("test_imports", job_id, user, "testcase.import")
    if job["status"] == 'CONFIRMED':
        return envelope(job)
    selected = payload.selected_indexes or list(range(len(job["preview"])))
    created = []
    for index in selected:
        if index < 0 or index >= len(job["preview"]):
            raise HTTPException(status_code=422, detail={"code": 'INVALID_PREVIEW_INDEX'})
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
                        "id": 'step-1',
                        "order": 1,
                        "action_doc": text_document(item["action"]),
                        "test_data": {},
                        "expected_doc": text_document(item["expected"]),
                    }
                ],
                test_data={},
                expected_result_doc=text_document(item["expected"]),
                postconditions_doc=text_document('Hoàn tất'),
                tags=item["tags"],
                origin='import',
            ),
            user,
        )
        created.append(draft)
    await test_design_repository.confirm_import(
        job_id,
        {
            "status": 'CONFIRMED',
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
    
    await get_project(project_id, user, "testcase.export")
    versions = await test_design_repository.list_case_versions(
        {"project_id": project_id},
        20000,
        'test_case_key',
        1,
    )
    
    rows = [[item.get(field) for field in ['test_case_key',
 'version',
 'title',
 'type',
 'priority',
 'risk',
 'automation_status',
 'status',
 'plain_text_projection']] for item in versions]
    if format == 'xlsx':
        content = create_xlsx([['test_case_key',
 'version',
 'title',
 'type',
 'priority',
 'risk',
 'automation_status',
 'status',
 'plain_text_projection'], *rows])
        return {
            "content": content,
            "media_type": 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            "filename": f"{'test-cases-'}{project_id}.xlsx",
        }
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=['test_case_key',
 'version',
 'title',
 'type',
 'priority',
 'risk',
 'automation_status',
 'status',
 'plain_text_projection'])
    writer.writeheader()
    for item in versions:
        writer.writerow({field: item.get(field) for field in ['test_case_key',
 'version',
 'title',
 'type',
 'priority',
 'risk',
 'automation_status',
 'status',
 'plain_text_projection']})
    return {
        "content": stream.getvalue(),
        "media_type": 'text/csv',
        "filename": f"{'test-cases-'}{project_id}.csv",
    }
