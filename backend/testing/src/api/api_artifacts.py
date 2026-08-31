import csv
import io
import json
import re
import zipfile
from xml.sax.saxutils import escape

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from src.api.requirements import extract_xlsx_csv
from src.api.test_design import create_test_case_draft, text_doc
from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, now
from src.core.database import database
from src.domain.schemas import ImportConfirm, ImportCreate, TestCaseDraftCreate
from src.services.linters import duplicate_score


router = APIRouter(prefix="/api/qa", tags=["QA API Artifacts and Recovery"])
SECRET_PATTERN = re.compile(r"token|secret|password|authorization|cookie|api[-_]?key", re.I)


@router.post("/projects/{project_id}/api-imports", status_code=201)
async def import_api_artifact(
    project_id: str,
    payload: ImportCreate,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "knowledge.manage")
    if payload.format not in {"openapi", "postman"}:
        raise HTTPException(status_code=422, detail={"code": "API_ARTIFACT_REQUIRED"})
    value = json.loads(payload.content) if isinstance(payload.content, str) else payload.content
    operations = parse_openapi(value) if payload.format == "openapi" else parse_postman(value)
    import_id = new_id("AIMP")
    documents = [{"_id": new_id("APIOP"), "project_id": project_id, "import_id": import_id, **item, "created_at": now()} for item in operations]
    if documents:
        await database.value.api_operations.insert_many(documents)
    job = {"_id": import_id, "project_id": project_id, "filename": payload.filename, "format": payload.format, "status": "CONFIRMED", "operation_ids": [item["_id"] for item in documents], "created_by": user.id, "created_at": now()}
    await database.value.api_imports.insert_one(job)
    await audit(user.id, "api_artifact_imported", "APIImport", import_id, project_id, {"operation_count": len(documents)})
    return envelope({**job, "operations": documents})


@router.get("/projects/{project_id}/api-operations")
async def list_api_operations(project_id: str, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "knowledge.read")
    return envelope(await database.value.api_operations.find({"project_id": project_id}).sort("path", 1).to_list(5000))


@router.post("/api-operations/{operation_id}/generate-tests", status_code=201)
async def generate_api_tests(operation_id: str, user: CurrentUser = Depends(get_current_user)):
    operation = await get_project_entity(
        "api_operations", operation_id, user, "ai.generate_testcase"
    )
    cases = api_case_blueprints(operation)
    created = []
    for case in cases:
        response = await create_test_case_draft(
            operation["project_id"],
            TestCaseDraftCreate(
                title=case["title"],
                type="api",
                priority="high" if case["category"] in {"auth", "forbidden", "conflict"} else "medium",
                risk="high" if case["category"] in {"auth", "schema_mismatch"} else "medium",
                preconditions_doc=text_doc(f"API operation {operation['method']} {operation['path']} tồn tại trong đặc tả"),
                steps=[{"id": "step-1", "order": 1, "action_doc": text_doc(case["action"]), "test_data": case["test_data"], "expected_doc": text_doc(case["expected"])}],
                test_data=case["test_data"],
                expected_result_doc=text_doc(case["expected"]),
                postconditions_doc=text_doc("Không lưu secret vào artifact kiểm thử"),
                tags=["api", case["category"]],
                automation_status="candidate",
                origin="ai_generated",
                source_evidence=[{"artifact_type": "api_operation", "artifact_version_id": operation_id, "path": operation["path"], "method": operation["method"]}],
            ),
            user,
        )
        created.append(response["data"])
    await audit(user.id, "api_tests_generated", "APIOperation", operation_id, operation["project_id"], {"count": len(created)})
    return envelope({"items": created, "model": model_metadata("api-test-generator-v1"), "evidence": operation})


@router.post("/projects/{project_id}/trace-recovery", status_code=201)
async def recover_trace_links(project_id: str, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "trace.recover")
    requirements = await database.value.requirement_versions.find({"project_id": project_id, "status": "BASELINED"}).to_list(5000)
    tests = await database.value.test_case_versions.find({"project_id": project_id, "status": "ACTIVE"}).to_list(10000)
    existing = await database.value.trace_links.find({"project_id": project_id, "status": {"$in": ["CONFIRMED", "SUGGESTED"]}}).to_list(50000)
    pairs = {(item["source_id"], item["target_id"]) for item in existing}
    suggestions = []
    for test in tests:
        ranked = sorted(((lexical_similarity(req.get("plain_text_projection", ""), test.get("plain_text_projection", "")), req) for req in requirements), key=lambda item: item[0], reverse=True)
        for score, requirement in ranked[:3]:
            if score < 0.18 or (requirement["_id"], test["_id"]) in pairs:
                continue
            link = {"_id": new_id("TL"), "project_id": project_id, "source_type": "requirement_version", "source_id": requirement["_id"], "target_type": "test_case_version", "target_id": test["_id"], "link_type": "verifies", "confidence": score, "origin": "trace_recovery", "status": "SUGGESTED", "evidence": [{"matched_terms": sorted(terms(requirement.get("plain_text_projection", "")) & terms(test.get("plain_text_projection", "")))}], "created_by": user.id, "created_at": now(), "updated_at": now()}
            suggestions.append(link)
    if suggestions:
        await database.value.trace_links.insert_many(suggestions)
    await audit(user.id, "trace_recovery_completed", "Project", project_id, project_id, {"suggestion_count": len(suggestions)})
    return envelope({"items": suggestions, "model": model_metadata("trace-recovery-v1")})


@router.post("/projects/{project_id}/test-case-imports", status_code=201)
async def preview_test_import(project_id: str, payload: ImportCreate, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "testcase.import")
    if payload.format not in {"csv", "xlsx"}:
        raise HTTPException(status_code=422, detail={"code": "TEST_IMPORT_FORMAT_UNSUPPORTED"})
    content = str(payload.content)
    rows = list(csv.DictReader(io.StringIO(content)))
    preview = [{"title": row.get("title") or f"Test Case dòng {index + 1}", "type": row.get("type") or "custom", "priority": row.get("priority") or "medium", "risk": row.get("risk") or "medium", "precondition": row.get("precondition") or "Hệ thống sẵn sàng", "action": row.get("action") or row.get("steps") or "Thực hiện thao tác", "expected": row.get("expected") or row.get("expected_result") or "Kết quả đúng theo đặc tả", "tags": [item.strip() for item in (row.get("tags") or "").split(",") if item.strip()]} for index, row in enumerate(rows[:5000])]
    job = {"_id": new_id("TIMP"), "project_id": project_id, "filename": payload.filename, "format": payload.format, "preview": preview, "status": "PREVIEW_READY", "created_by": user.id, "created_at": now()}
    await database.value.test_imports.insert_one(job)
    return envelope(job)


@router.post("/projects/{project_id}/test-case-imports/upload", status_code=201)
async def upload_test_import(
    project_id: str,
    format: str = Form(),
    file: UploadFile = File(),
    user: CurrentUser = Depends(get_current_user),
):
    if format not in {"csv", "xlsx"}:
        raise HTTPException(status_code=422, detail={"code": "TEST_IMPORT_FORMAT_UNSUPPORTED"})
    data = await file.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail={"code": "IMPORT_TOO_LARGE"})
    content = extract_xlsx_csv(data) if format == "xlsx" else data.decode("utf-8-sig")
    return await preview_test_import(
        project_id,
        ImportCreate(filename=file.filename or f"test-cases.{format}", format=format, content=content),
        user,
    )


@router.post("/test-case-imports/{job_id}/confirm")
async def confirm_test_import(job_id: str, payload: ImportConfirm, user: CurrentUser = Depends(get_current_user)):
    job = await get_project_entity(
        "test_imports", job_id, user, "testcase.import"
    )
    if job["status"] == "CONFIRMED":
        return envelope(job)
    selected = payload.selected_indexes or list(range(len(job["preview"])))
    created = []
    for index in selected:
        if index < 0 or index >= len(job["preview"]):
            raise HTTPException(status_code=422, detail={"code": "INVALID_PREVIEW_INDEX"})
        item = job["preview"][index]
        response = await create_test_case_draft(job["project_id"], TestCaseDraftCreate(title=item["title"], type=item["type"], priority=item["priority"], risk=item["risk"], preconditions_doc=text_doc(item["precondition"]), steps=[{"id": "step-1", "order": 1, "action_doc": text_doc(item["action"]), "test_data": {}, "expected_doc": text_doc(item["expected"])}], test_data={}, expected_result_doc=text_doc(item["expected"]), postconditions_doc=text_doc("Hoàn tất"), tags=item["tags"], origin="import"), user)
        created.append(response["data"])
    await database.value.test_imports.update_one({"_id": job_id}, {"$set": {"status": "CONFIRMED", "created_draft_ids": [item["_id"] for item in created], "confirmed_at": now()}})
    return envelope({"job_id": job_id, "drafts": created})


@router.get("/projects/{project_id}/test-cases/export")
async def export_test_cases(
    project_id: str,
    format: str = Query("csv", pattern="^(csv|xlsx)$"),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "testcase.export")
    versions = await database.value.test_case_versions.find({"project_id": project_id}).sort("test_case_key", 1).to_list(20000)
    fields = ["test_case_key", "version", "title", "type", "priority", "risk", "automation_status", "status", "plain_text_projection"]
    rows = [[item.get(field) for field in fields] for item in versions]
    if format == "xlsx":
        content = create_xlsx([fields, *rows])
        return StreamingResponse(
            iter([content]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="test-cases-{project_id}.xlsx"'},
        )
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for item in versions:
        writer.writerow({field: item.get(field) for field in fields})
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="test-cases-{project_id}.csv"'})


def create_xlsx(rows):
    sheet_rows = []
    for row_index, row in enumerate(rows, 1):
        cells = []
        for column_index, value in enumerate(row, 1):
            reference = f"{xlsx_column(column_index)}{row_index}"
            normalized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", "" if value is None else str(value))
            cells.append(f'<c r="{reference}" t="inlineStr"><is><t xml:space="preserve">{escape(normalized)}</t></is></c>')
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    content_types = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'
    root_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    workbook = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Test Cases" sheetId="1" r:id="rId1"/></sheets></workbook>'
    workbook_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
    worksheet = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{"".join(sheet_rows)}</sheetData></worksheet>'
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)
    return output.getvalue()


def xlsx_column(index):
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def parse_openapi(value):
    operations = []
    inherited_security = value.get("security", [])
    schemas = value.get("components", {}).get("schemas", {})
    for path, path_item in value.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                continue
            operations.append({"source_type": "openapi", "operation_id": operation.get("operationId"), "title": operation.get("summary") or f"{method.upper()} {path}", "path": path, "method": method.upper(), "parameters": sanitize(operation.get("parameters", []) + path_item.get("parameters", [])), "request_body": sanitize(operation.get("requestBody", {})), "responses": sanitize(operation.get("responses", {})), "security": sanitize(operation.get("security", inherited_security)), "schemas": sanitize(schemas), "tags": operation.get("tags", [])})
    return operations[:5000]


def parse_postman(value):
    operations = []
    variable_names = [item.get("key") for item in value.get("variable", []) if item.get("key") and not SECRET_PATTERN.search(item.get("key", ""))]
    def walk(nodes, folder=""):
        for node in nodes:
            if "item" in node:
                walk(node["item"], "/".join(filter(None, [folder, node.get("name", "")])))
                continue
            request = node.get("request")
            if not request:
                continue
            url = request.get("url", {})
            raw = url.get("raw", "") if isinstance(url, dict) else str(url)
            operations.append({"source_type": "postman", "operation_id": node.get("id"), "title": node.get("name") or f"{request.get('method', 'GET')} {raw}", "folder": folder, "path": raw.split("?", 1)[0], "method": request.get("method", "GET").upper(), "header_names": [item.get("key") for item in request.get("header", []) if item.get("key") and not SECRET_PATTERN.search(item.get("key", ""))], "body": sanitize(request.get("body", {})), "script_events": [item.get("listen") for item in node.get("event", [])], "variable_names": variable_names})
    walk(value.get("item", []))
    return operations[:5000]


def api_case_blueprints(operation):
    responses = operation.get("responses", {})
    response_codes = list(responses)
    success = next((code for code in response_codes if str(code).startswith("2")), "2xx theo đặc tả")
    cases = [{"category": "success", "title": f"{operation['method']} {operation['path']} thành công", "action": "Gửi request hợp lệ theo schema", "test_data": {}, "expected": f"Response {success} và schema đúng đặc tả"}]
    parameter_names = [item.get("name") for item in operation.get("parameters", []) if item.get("required")]
    if parameter_names:
        cases.append({"category": "required_missing", "title": f"Thiếu trường bắt buộc {parameter_names[0]}", "action": f"Gửi request không có {parameter_names[0]}", "test_data": {"missing": parameter_names[0]}, "expected": expected_error(responses, ["400", "422"], "lỗi validation theo đặc tả")})
    for category, candidates, action in [("auth", ["401"], "Gửi request không có thông tin xác thực"), ("forbidden", ["403"], "Gửi request với quyền không đủ"), ("not_found", ["404"], "Gửi request tới tài nguyên không tồn tại"), ("conflict", ["409"], "Gửi request gây xung đột trạng thái"), ("schema_mismatch", ["400", "422"], "Gửi request sai kiểu dữ liệu")]:
        matched = next((code for code in candidates if code in responses), None)
        if matched:
            cases.append({"category": category, "title": f"{operation['method']} {operation['path']} {category}", "action": action, "test_data": {}, "expected": f"Response {matched} và schema đúng đặc tả"})
    return cases


def expected_error(responses, candidates, fallback):
    code = next((value for value in candidates if value in responses), None)
    return f"Response {code} và schema đúng đặc tả" if code else fallback


def sanitize(value):
    if isinstance(value, dict):
        return {key: sanitize(item) for key, item in value.items() if not SECRET_PATTERN.search(str(key))}
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    return value


def terms(value):
    return {item for item in re.findall(r"[a-zA-Z0-9_]+", value.lower()) if len(item) > 2}


def lexical_similarity(left, right):
    left_terms = terms(left)
    right_terms = terms(right)
    union = left_terms | right_terms
    return round(len(left_terms & right_terms) / len(union), 4) if union else 0


def model_metadata(model):
    return {"provider": "hybrid-deterministic", "model": model, "prompt_version": "qa-v1", "tool_schema_version": "1", "retrieval_version": "project-filter-v1", "created_at": now()}
