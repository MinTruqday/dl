import csv
import io
import json
import zipfile
from xml.etree import ElementTree

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pypdf import PdfReader
from pymongo.errors import DuplicateKeyError

from src.core.auth import CurrentUser, get_current_user
from src.core.common import (
    audit,
    envelope,
    get_project,
    get_project_entity,
    new_id,
    next_key,
    now,
    plain_text,
    validate_doc,
)
from src.core.database import database
from src.domain.schemas import (
    ImportConfirm,
    ImportCreate,
    RequirementBaselineInput,
    RequirementCompareInput,
    RequirementCreate,
    RequirementVersionCreate,
)
from src.services.change_analysis import semantic_changes
from src.services.linters import requirement_findings
from src.services.project_rag import index_artifact


router = APIRouter(prefix="/api/qa", tags=["QA Requirements"])


async def persist_acceptance_criteria(version, values):
    criteria = []
    for value in values:
        item = value.model_dump() if hasattr(value, "model_dump") else dict(value)
        validate_doc(item["content_doc"])
        criterion = {
            "_id": new_id("AC"),
            "project_id": version["project_id"],
            "requirement_version_id": version["_id"],
            **item,
            "plain_text": plain_text(item["content_doc"]),
            "created_at": now(),
        }
        criteria.append(criterion)
    if criteria:
        await database.value.acceptance_criteria.insert_many(criteria)
    await database.value.requirement_versions.update_one(
        {"_id": version["_id"]},
        {"$set": {"acceptance_criterion_ids": [item["_id"] for item in criteria]}},
    )
    version["acceptance_criterion_ids"] = [item["_id"] for item in criteria]
    version["acceptance_criteria"] = criteria
    return version


async def create_requirement_record(project_id, payload, user, origin="manual"):
    await get_project(project_id, user, write=True)
    validate_doc(payload.content_doc)
    requirement_key = payload.requirement_key or await next_key(project_id, "requirement", "REQ")
    timestamp = now()
    requirement_id = new_id("REQ")
    version = {
        "_id": new_id("REQV"),
        "project_id": project_id,
        "requirement_id": requirement_id,
        "requirement_key": requirement_key,
        "version": 1,
        "title": payload.title,
        "type": payload.type,
        "priority": payload.priority,
        "risk": payload.risk,
        "content_doc": payload.content_doc,
        "plain_text_projection": plain_text(payload.content_doc),
        "business_rules": payload.business_rules,
        "actors": payload.actors,
        "dependencies": payload.dependencies,
        "source_refs": payload.source_refs,
        "acceptance_criterion_ids": [],
        "parent_version_id": None,
        "change_reason": "Khởi tạo Requirement",
        "status": "DRAFT",
        "revision": 1,
        "origin": origin,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    requirement = {
        "_id": requirement_id,
        "project_id": project_id,
        "requirement_key": requirement_key,
        "current_version_id": version["_id"],
        "status": "DRAFT",
        "owner_id": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await database.value.requirements.insert_one(requirement)
        await database.value.requirement_versions.insert_one(version)
    except DuplicateKeyError:
        await database.value.requirements.delete_one({"_id": requirement_id})
        raise HTTPException(status_code=409, detail={"code": "REQUIREMENT_KEY_EXISTS"})
    await persist_acceptance_criteria(version, payload.acceptance_criteria)
    await index_requirement(version)
    await audit(user.id, "requirement_created", "Requirement", requirement_id, project_id)
    return {**requirement, "current_version": version}


@router.post("/projects/{project_id}/requirements", status_code=201)
async def create_requirement(
    project_id: str,
    payload: RequirementCreate,
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(await create_requirement_record(project_id, payload, user))


@router.get("/projects/{project_id}/requirements")
async def list_requirements(
    project_id: str,
    q: str = Query(default="", max_length=300),
    status: str = Query(default="", max_length=30),
    limit: int = Query(default=100, ge=1, le=500),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user)
    query = {"project_id": project_id}
    if q:
        query["$or"] = [
            {"requirement_key": {"$regex": q, "$options": "i"}},
        ]
    if status:
        query["status"] = status
    requirements = await database.value.requirements.find(query).sort("updated_at", -1).to_list(limit)
    version_ids = [item.get("current_version_id") for item in requirements]
    versions = await database.value.requirement_versions.find({"_id": {"$in": version_ids}}).to_list(limit)
    by_id = {item["_id"]: item for item in versions}
    items = [{**item, "current_version": by_id.get(item.get("current_version_id"))} for item in requirements]
    if q:
        lowered = q.lower()
        items = [
            item
            for item in items
            if lowered in item["requirement_key"].lower()
            or lowered in str(item.get("current_version", {}).get("title", "")).lower()
        ]
    return envelope(items)


@router.get("/requirements/{requirement_id}")
async def requirement_detail(requirement_id: str, user: CurrentUser = Depends(get_current_user)):
    requirement = await get_project_entity("requirements", requirement_id, user)
    version = await database.value.requirement_versions.find_one({"_id": requirement["current_version_id"]})
    criteria = await database.value.acceptance_criteria.find({"requirement_version_id": version["_id"]}).to_list(500)
    return envelope({**requirement, "current_version": {**version, "acceptance_criteria": criteria}})


@router.post("/requirements/{requirement_id}/versions", status_code=201)
async def create_requirement_version(
    requirement_id: str,
    payload: RequirementVersionCreate,
    user: CurrentUser = Depends(get_current_user),
):
    requirement = await get_project_entity("requirements", requirement_id, user, write=True)
    if requirement["current_version_id"] != payload.expected_current_version_id:
        raise HTTPException(
            status_code=409,
            detail={"code": "REVISION_CONFLICT", "current_version_id": requirement["current_version_id"]},
        )
    parent = await database.value.requirement_versions.find_one({"_id": requirement["current_version_id"]})
    latest = await database.value.requirement_versions.find_one(
        {"requirement_id": requirement_id}, sort=[("version", -1)]
    )
    timestamp = now()
    version = {
        "_id": new_id("REQV"),
        "project_id": requirement["project_id"],
        "requirement_id": requirement_id,
        "requirement_key": requirement["requirement_key"],
        "version": int(latest.get("version", 0)) + 1,
        "title": payload.title,
        "type": payload.type,
        "priority": payload.priority,
        "risk": payload.risk,
        "content_doc": validate_doc(payload.content_doc),
        "plain_text_projection": plain_text(payload.content_doc),
        "business_rules": payload.business_rules,
        "actors": payload.actors,
        "dependencies": payload.dependencies,
        "source_refs": payload.source_refs,
        "acceptance_criterion_ids": [],
        "parent_version_id": parent["_id"],
        "change_reason": payload.change_reason,
        "status": "DRAFT",
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    await database.value.requirement_versions.insert_one(version)
    await persist_acceptance_criteria(version, payload.acceptance_criteria)
    await index_requirement(version)
    await database.value.requirements.update_one(
        {"_id": requirement_id},
        {"$set": {"current_version_id": version["_id"], "status": "CHANGED", "updated_at": timestamp}},
    )
    await audit(user.id, "requirement_version_created", "RequirementVersion", version["_id"], requirement["project_id"], {"parent_version_id": parent["_id"]})
    return envelope(version, revision=1)


@router.get("/requirements/{requirement_id}/versions")
async def list_requirement_versions(requirement_id: str, user: CurrentUser = Depends(get_current_user)):
    requirement = await get_project_entity("requirements", requirement_id, user)
    versions = await database.value.requirement_versions.find({"requirement_id": requirement_id}).sort("version", -1).to_list(500)
    return envelope(versions)


@router.post("/requirement-versions/{version_id}/baseline")
async def baseline_requirement_version(
    version_id: str,
    payload: RequirementBaselineInput,
    user: CurrentUser = Depends(get_current_user),
):
    version = await get_project_entity("requirement_versions", version_id, user, write=True)
    if version["status"] == "BASELINED":
        return envelope(version, revision=version["revision"])
    if version["status"] not in {"DRAFT", "IN_REVIEW", "APPROVED"}:
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    if version["revision"] != payload.expected_revision:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT", "current_revision": version["revision"]})
    findings = requirement_findings(version)
    if any(item["severity"] == "error" for item in findings):
        raise HTTPException(status_code=409, detail={"code": "REQUIREMENT_LINT_BLOCKED", "findings": findings})
    timestamp = now()
    await database.value.requirement_versions.update_one(
        {"_id": version_id, "revision": payload.expected_revision},
        {"$set": {"status": "BASELINED", "baselined_at": timestamp, "baselined_by": user.id, "updated_at": timestamp}, "$inc": {"revision": 1}},
    )
    await database.value.requirements.update_one(
        {"_id": version["requirement_id"]},
        {"$set": {"current_version_id": version_id, "status": "BASELINED", "updated_at": timestamp}},
    )
    version = await database.value.requirement_versions.find_one({"_id": version_id})
    await index_requirement(version)
    await audit(user.id, "requirement_version_baselined", "RequirementVersion", version_id, version["project_id"])
    return envelope(version, revision=version["revision"])


@router.post("/requirement-versions/{version_id}/ai/lint")
async def lint_requirement(version_id: str, user: CurrentUser = Depends(get_current_user)):
    version = await get_project_entity("requirement_versions", version_id, user)
    findings = requirement_findings(version)
    result = {
        "requirement_version_id": version_id,
        "findings": findings,
        "valid": not any(item["severity"] == "error" for item in findings),
        "model": {"provider": "rules", "model": "requirement-linter-v1", "prompt_version": "qa-v1", "tool_schema_version": "1"},
    }
    await database.value.ai_findings.insert_one({"_id": new_id("AIF"), "project_id": version["project_id"], "artifact_type": "requirement_version", "artifact_id": version_id, **result, "created_at": now()})
    return envelope(result)


@router.post("/requirements/{requirement_id}/compare")
async def compare_requirement(
    requirement_id: str,
    payload: RequirementCompareInput,
    user: CurrentUser = Depends(get_current_user),
):
    requirement = await get_project_entity("requirements", requirement_id, user)
    versions = await database.value.requirement_versions.find(
        {"requirement_id": requirement_id, "_id": {"$in": [payload.from_version_id, payload.to_version_id]}}
    ).to_list(2)
    by_id = {item["_id"]: item for item in versions}
    if set(by_id) != {payload.from_version_id, payload.to_version_id}:
        raise HTTPException(status_code=404, detail="Không tìm thấy đủ hai phiên bản")
    changes = semantic_changes(by_id[payload.from_version_id], by_id[payload.to_version_id])
    return envelope({"from_version": by_id[payload.from_version_id], "to_version": by_id[payload.to_version_id], "changes": changes})


@router.post("/projects/{project_id}/requirement-imports", status_code=201)
async def create_requirement_import(
    project_id: str,
    payload: ImportCreate,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, write=True)
    previews = parse_import(payload)
    job = {
        "_id": new_id("RIMP"),
        "project_id": project_id,
        "filename": payload.filename,
        "format": payload.format,
        "status": "PREVIEW_READY",
        "preview": previews,
        "created_by": user.id,
        "created_at": now(),
    }
    await database.value.import_jobs.insert_one(job)
    await audit(user.id, "requirement_import_previewed", "RequirementImport", job["_id"], project_id, {"count": len(previews)})
    return envelope(job)


@router.post("/projects/{project_id}/requirement-imports/upload", status_code=201)
async def upload_requirement_import(
    project_id: str,
    format: str = Form(),
    file: UploadFile = File(),
    user: CurrentUser = Depends(get_current_user),
):
    if format not in {"pdf", "docx", "md", "txt", "csv", "xlsx", "openapi", "postman"}:
        raise HTTPException(status_code=422, detail={"code": "UNSUPPORTED_IMPORT_FORMAT"})
    data = await file.read(25 * 1024 * 1024 + 1)
    if not data:
        raise HTTPException(status_code=422, detail={"code": "EMPTY_IMPORT"})
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail={"code": "IMPORT_TOO_LARGE"})
    content = extract_file_content(data, format)
    return await create_requirement_import(
        project_id,
        ImportCreate(filename=file.filename or f"requirements.{format}", format=format, content=content),
        user,
    )


@router.get("/requirement-imports/{job_id}")
async def get_requirement_import(job_id: str, user: CurrentUser = Depends(get_current_user)):
    return envelope(await get_project_entity("import_jobs", job_id, user))


@router.post("/requirement-imports/{job_id}/confirm")
async def confirm_requirement_import(
    job_id: str,
    payload: ImportConfirm,
    user: CurrentUser = Depends(get_current_user),
):
    job = await get_project_entity("import_jobs", job_id, user, write=True)
    if job["status"] == "CONFIRMED":
        return envelope(job)
    indexes = payload.selected_indexes or list(range(len(job["preview"])))
    created = []
    for index in indexes:
        if index < 0 or index >= len(job["preview"]):
            raise HTTPException(status_code=422, detail="Chỉ mục preview không hợp lệ")
        item = job["preview"][index]
        created.append(
            await create_requirement_record(
                job["project_id"],
                RequirementCreate(**item),
                user,
                origin="import",
            )
        )
    await database.value.import_jobs.update_one(
        {"_id": job_id},
        {"$set": {"status": "CONFIRMED", "created_requirement_ids": [item["_id"] for item in created], "confirmed_at": now()}},
    )
    return envelope({"job_id": job_id, "requirements": created})


def parse_import(payload):
    content = payload.content
    if payload.format in {"openapi", "postman"}:
        value = json.loads(content) if isinstance(content, str) else content
        return parse_api_artifact(value, payload.format)
    if payload.format == "csv":
        rows = list(csv.DictReader(io.StringIO(str(content))))
        return [
            {
                "requirement_key": row.get("requirement_key") or None,
                "title": row.get("title") or f"Requirement nhập dòng {index + 1}",
                "type": row.get("type") or "functional",
                "priority": row.get("priority") or "medium",
                "risk": row.get("risk") or "medium",
                "content_doc": text_doc(row.get("content") or row.get("description") or ""),
                "acceptance_criteria": [],
            }
            for index, row in enumerate(rows)
        ]
    text = str(content)
    blocks = [block.strip() for block in text.split("\n\n") if block.strip()]
    return [
        {
            "title": block.splitlines()[0][:300],
            "content_doc": text_doc(block),
            "acceptance_criteria": [],
        }
        for block in blocks[:500]
    ]


def extract_file_content(data, format):
    if format == "pdf":
        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    if format == "docx":
        return extract_docx(data)
    if format == "xlsx":
        return extract_xlsx_csv(data)
    text = data.decode("utf-8-sig")
    if format in {"openapi", "postman"}:
        return json.loads(text)
    return text


def extract_docx(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs = []
    for paragraph in root.iter(f"{namespace}p"):
        text = "".join(node.text or "" for node in paragraph.iter(f"{namespace}t")).strip()
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs)


def extract_xlsx_csv(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = set(archive.namelist())
        shared = []
        if "xl/sharedStrings.xml" in names:
            root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(node.text or "" for node in item.iter() if node.tag.endswith("}t")) for item in root]
        sheets = sorted(name for name in names if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"))
        rows = []
        for sheet in sheets:
            root = ElementTree.fromstring(archive.read(sheet))
            for row in (node for node in root.iter() if node.tag.endswith("}row")):
                values = []
                for cell in (node for node in row if node.tag.endswith("}c")):
                    cell_type = cell.attrib.get("t")
                    if cell_type == "inlineStr":
                        value = "".join(node.text or "" for node in cell.iter() if node.tag.endswith("}t"))
                    else:
                        value_node = next((node for node in cell if node.tag.endswith("}v")), None)
                        value = value_node.text if value_node is not None else ""
                    if cell_type == "s" and value:
                        value = shared[int(value)]
                    values.append(value or "")
                rows.append(values)
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerows(rows)
    return stream.getvalue()


def parse_api_artifact(value, artifact_format):
    items = []
    if artifact_format == "openapi":
        for path, operations in value.get("paths", {}).items():
            for method, operation in operations.items():
                if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                    continue
                items.append(
                    {
                        "title": operation.get("summary") or f"{method.upper()} {path}",
                        "type": "api",
                        "content_doc": text_doc(json.dumps({"path": path, "method": method, "parameters": operation.get("parameters", []), "responses": operation.get("responses", {}), "security": operation.get("security", [])}, ensure_ascii=False)),
                        "source_refs": [{"type": "openapi", "path": path, "method": method}],
                        "acceptance_criteria": [],
                    }
                )
    else:
        def walk(nodes, folder=""):
            for node in nodes:
                if "item" in node:
                    walk(node["item"], "/".join(filter(None, [folder, node.get("name", "")])))
                elif "request" in node:
                    request = node["request"]
                    url = request.get("url", {})
                    raw_url = url.get("raw", "") if isinstance(url, dict) else str(url)
                    items.append(
                        {
                            "title": node.get("name") or f"{request.get('method', 'GET')} {raw_url}",
                            "type": "api",
                            "content_doc": text_doc(json.dumps({"folder": folder, "method": request.get("method"), "url_template": redact_url(raw_url), "header_names": [header.get("key") for header in request.get("header", [])]}, ensure_ascii=False)),
                            "source_refs": [{"type": "postman", "folder": folder}],
                            "acceptance_criteria": [],
                        }
                    )
        walk(value.get("item", []))
    return items[:1000]


def redact_url(value):
    return value.split("?")[0]


def text_doc(value):
    return {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": str(value)}]}]}


async def index_requirement(version):
    await index_artifact(version["project_id"], "requirement_version", version["requirement_id"], version["_id"], version["title"], version.get("plain_text_projection", ""), version.get("status", "DRAFT"), "baseline" if version.get("status") == "BASELINED" else "draft", version.get("version"))
