import csv
import hashlib
import io
import json
import re
import zipfile
from xml.etree import ElementTree

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pypdf import PdfReader
from pymongo import ReturnDocument
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
    page_payload,
    plain_text,
    sort_spec,
    validate_doc,
)
from src.core.database import database
from src.core.configuration import settings
from src.domain.schemas import (
    ImportConfirm,
    ImportCreate,
    RequirementBaselineInput,
    RequirementCompareInput,
    RequirementCreate,
    RequirementDraftPatch,
    RequirementExtractionInput,
    RequirementImportReview,
    RequirementObsoleteInput,
    RequirementParseRetry,
    RequirementVersionCreate,
    ReviewTransitionInput,
)
from src.services.change_analysis import semantic_changes
from src.services.linters import requirement_findings
from src.services.project_knowledge import index_artifact


router = APIRouter(prefix="/api/qa", tags=["QA Requirements"])


def serialized_content(content):
    if isinstance(content, str):
        return content
    return json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


async def create_requirement_document_record(project_id, payload, user):
    await get_project(project_id, user, "requirement.create")
    content = serialized_content(payload.content)
    if len(content.encode("utf-8")) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail={"code": "IMPORT_TOO_LARGE"})
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    existing = await database.value.requirement_documents.find_one(
        {"project_id": project_id, "content_hash": content_hash}
    )
    if existing:
        return existing
    timestamp = now()
    document = {
        "_id": new_id("RDOC"),
        "project_id": project_id,
        "filename": payload.filename,
        "format": payload.format,
        "content_hash": content_hash,
        "raw_source": {
            "storage": "embedded",
            "content": payload.content,
            "sha256": content_hash,
            "size": len(content.encode("utf-8")),
        },
        "normalized_content": payload.content,
        "normalized_content_hash": content_hash,
        "status": "READY",
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await database.value.requirement_documents.insert_one(document)
    except DuplicateKeyError:
        existing = await database.value.requirement_documents.find_one(
            {"project_id": project_id, "content_hash": content_hash}
        )
        if existing:
            return existing
        raise
    await audit(
        user.id,
        "requirement_document_created",
        "RequirementDocument",
        document["_id"],
        project_id,
        {"content_hash": content_hash, "format": payload.format},
    )
    return document


async def store_raw_requirement_source(project_id, document_id, filename, content_type, data):
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{settings.CLOUD_URL.rstrip('/')}/noi-bo/qa/requirement-source",
            headers={"X-Internal-Token": settings.SECRET_KEY},
            data={"project_id": project_id, "document_id": document_id},
            files={"file": (filename, data, content_type or "application/octet-stream")},
        )
    response.raise_for_status()
    return response.json()["data"]


async def read_raw_requirement_source(document):
    source = document.get("raw_source") or {}
    if source.get("storage") == "embedded":
        content = serialized_content(source.get("content"))
        return content.encode("utf-8")
    object_key = source.get("object_key")
    if not object_key:
        raise HTTPException(status_code=409, detail={"code": "RAW_SOURCE_UNAVAILABLE"})
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(
            f"{settings.CLOUD_URL.rstrip('/')}/noi-bo/qa/requirement-source",
            headers={"X-Internal-Token": settings.SECRET_KEY},
            params={
                "project_id": document["project_id"],
                "document_id": document["_id"],
                "object_key": object_key,
            },
        )
    response.raise_for_status()
    return response.content


async def persist_acceptance_criteria(version, values):
    criteria = []
    keys = [value.key if hasattr(value, "key") else value.get("key") for value in values]
    if len(keys) != len(set(keys)):
        raise HTTPException(status_code=422, detail={"code": "DUPLICATE_ACCEPTANCE_CRITERION_KEY"})
    for value in values:
        item = value.model_dump() if hasattr(value, "model_dump") else dict(value)
        if version.get("status") == "DRAFT" and item.get("status") != "obsolete":
            item["status"] = "draft"
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
    await get_project(project_id, user, "requirement.create")
    await validate_requirement_sources(project_id, payload.source_refs)
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
        "tags": payload.tags,
        "owner_id": payload.owner_id or user.id,
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
        "owner_id": payload.owner_id or user.id,
        "tags": payload.tags,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await database.value.requirements.insert_one(requirement)
        await database.value.requirement_versions.insert_one(version)
    except DuplicateKeyError:
        await database.value.requirements.delete_one({"_id": requirement_id})
        raise HTTPException(status_code=409, detail={"code": "REQUIREMENT_KEY_EXISTS"})
    try:
        await persist_acceptance_criteria(version, payload.acceptance_criteria)
    except Exception:
        await database.value.acceptance_criteria.delete_many({"requirement_version_id": version["_id"]})
        await database.value.requirement_versions.delete_one({"_id": version["_id"], "project_id": project_id})
        await database.value.requirements.delete_one({"_id": requirement_id, "project_id": project_id})
        raise
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
    key: str = Query(default="", max_length=80),
    title: str = Query(default="", max_length=300),
    status: str = Query(default="", max_length=30),
    owner: str = Query(default="", max_length=200),
    tag: str = Query(default="", max_length=100),
    coverage: str = Query(default="", max_length=20),
    source_type: str = Query(default="", max_length=80),
    has_pending_impact: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    sort: str = Query(default="-updated_at", max_length=80),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "requirement.read")
    query = {"project_id": project_id}
    if status:
        query["status"] = status
    requirements = await database.value.requirements.find(query).to_list(20000)
    version_ids = [item.get("current_version_id") for item in requirements if item.get("current_version_id")]
    versions = await database.value.requirement_versions.find(
        {"project_id": project_id, "_id": {"$in": version_ids}}
    ).to_list(20000)
    by_id = {item["_id"]: item for item in versions}
    items = [{**item, "current_version": by_id.get(item.get("current_version_id"))} for item in requirements]
    confirmed_links = await database.value.trace_links.find(
        {
            "project_id": project_id,
            "status": "CONFIRMED",
            "source_type": "requirement_version",
            "source_id": {"$in": version_ids},
        },
        {"source_id": 1},
    ).to_list(50000)
    covered_ids = {item["source_id"] for item in confirmed_links}
    change_sets = await database.value.requirement_change_sets.find(
        {
            "project_id": project_id,
            "to_version_id": {"$in": version_ids},
            "status": {"$nin": ["REVIEWED", "CLOSED", "REJECTED"]},
        },
        {"to_version_id": 1},
    ).to_list(20000)
    pending_ids = {item["to_version_id"] for item in change_sets}
    for item in items:
        version = item.get("current_version") or {}
        item["owner_id"] = item.get("owner_id") or version.get("owner_id")
        item["tags"] = sorted(set(item.get("tags", [])) | set(version.get("tags", [])))
        item["covered"] = item.get("current_version_id") in covered_ids
        item["has_pending_impact"] = item.get("current_version_id") in pending_ids
        item["source_types"] = sorted(
            {
                str(ref.get("source_type") or ref.get("type") or "manual")
                for ref in version.get("source_refs", [])
            }
        )
    terms = [value.strip().lower() for value in (q, key, title) if value.strip()]
    if terms:
        def matches_requirement(item):
            version = item.get("current_version") or {}
            searchable = f"{item.get('requirement_key', '')} {version.get('title', '')}".lower()
            return all(value in searchable for value in terms)
        items = [item for item in items if matches_requirement(item)]
    if owner:
        items = [item for item in items if item.get("owner_id") == owner]
    if tag:
        items = [item for item in items if tag in item.get("tags", [])]
    if coverage:
        normalized = coverage.lower()
        if normalized not in {"covered", "uncovered"}:
            raise HTTPException(status_code=422, detail={"code": "INVALID_COVERAGE_FILTER"})
        items = [item for item in items if item.get("covered") is (normalized == "covered")]
    if source_type:
        items = [item for item in items if source_type in item.get("source_types", [])]
    if has_pending_impact is not None:
        items = [item for item in items if item.get("has_pending_impact") is has_pending_impact]
    sort_field, direction = sort_spec(
        sort,
        {"requirement_key", "status", "updated_at", "created_at", "title", "owner_id"},
    )
    items.sort(
        key=lambda item: str(
            (item.get("current_version") or {}).get(sort_field, item.get(sort_field, "")) or ""
        ).lower(),
        reverse=direction < 0,
    )
    total = len(items)
    start = (page - 1) * page_size
    return envelope(page_payload(items[start : start + page_size], page, page_size, total))


@router.get("/requirements/{requirement_id}")
async def requirement_detail(requirement_id: str, user: CurrentUser = Depends(get_current_user)):
    requirement = await get_project_entity(
        "requirements", requirement_id, user, "requirement.read"
    )
    version = await database.value.requirement_versions.find_one({"_id": requirement["current_version_id"]})
    criteria = await database.value.acceptance_criteria.find({"requirement_version_id": version["_id"]}).to_list(500)
    return envelope({**requirement, "current_version": {**version, "acceptance_criteria": criteria}})


@router.patch("/projects/{project_id}/requirements/{requirement_id}")
async def update_requirement_draft(
    project_id: str,
    requirement_id: str,
    payload: RequirementDraftPatch,
    user: CurrentUser = Depends(get_current_user),
):
    requirement = await get_project_entity("requirements", requirement_id, user, "requirement.update")
    if requirement["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    version = await database.value.requirement_versions.find_one(
        {"_id": requirement["current_version_id"], "project_id": project_id}
    )
    if not version or version.get("status") != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "IMMUTABLE_REQUIREMENT_VERSION"})
    if version.get("revision") != payload.expected_revision:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT", "current_revision": version.get("revision")})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    criteria = changes.pop("acceptance_criteria", None)
    if criteria is not None:
        keys = [item.key for item in criteria]
        if len(keys) != len(set(keys)):
            raise HTTPException(status_code=422, detail={"code": "DUPLICATE_ACCEPTANCE_CRITERION_KEY"})
        for item in criteria:
            validate_doc(item.content_doc)
    if "source_refs" in changes:
        await validate_requirement_sources(project_id, changes["source_refs"])
    content_doc = changes.get("content_doc")
    if content_doc is not None:
        validate_doc(content_doc)
        changes["plain_text_projection"] = plain_text(content_doc)
    if "requirement_key" in changes and changes["requirement_key"] != requirement.get("requirement_key"):
        duplicate = await database.value.requirements.find_one({"project_id": project_id, "requirement_key": changes["requirement_key"], "_id": {"$ne": requirement_id}})
        if duplicate:
            raise HTTPException(status_code=409, detail={"code": "REQUIREMENT_KEY_EXISTS"})
    updated_version = await database.value.requirement_versions.find_one_and_update(
        {"_id": version["_id"], "project_id": project_id, "status": "DRAFT", "revision": payload.expected_revision},
        {"$set": {**changes, "updated_at": now()}, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated_version:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    identity_changes = {
        key: changes[key]
        for key in ("owner_id", "tags")
        if key in changes
    }
    if identity_changes:
        await database.value.requirements.update_one(
            {"_id": requirement_id, "project_id": project_id, "current_version_id": version["_id"]},
            {"$set": {**identity_changes, "updated_at": now()}},
        )
    if criteria is not None:
        previous_criteria = await database.value.acceptance_criteria.find({"requirement_version_id": version["_id"]}).to_list(500)
        await database.value.acceptance_criteria.delete_many({"requirement_version_id": version["_id"]})
        try:
            await persist_acceptance_criteria(updated_version, criteria)
        except Exception:
            await database.value.acceptance_criteria.delete_many({"requirement_version_id": version["_id"]})
            if previous_criteria:
                await database.value.acceptance_criteria.insert_many(previous_criteria)
            await database.value.requirement_versions.update_one(
                {"_id": version["_id"], "project_id": project_id},
                {"$set": {"acceptance_criterion_ids": [item["_id"] for item in previous_criteria]}},
            )
            raise
        updated_version = await database.value.requirement_versions.find_one({"_id": version["_id"]})
    parent_changes = {key: changes[key] for key in ("requirement_key",) if key in changes}
    if parent_changes:
        await database.value.requirements.update_one({"_id": requirement_id, "project_id": project_id}, {"$set": {**parent_changes, "updated_at": now()}})
    await audit(user.id, "requirement_draft_updated", "Requirement", requirement_id, project_id)
    return envelope({**requirement, **parent_changes, "current_version": updated_version}, revision=updated_version["revision"])


@router.post("/requirements/{requirement_id}/versions", status_code=201)
async def create_requirement_version(
    requirement_id: str,
    payload: RequirementVersionCreate,
    user: CurrentUser = Depends(get_current_user),
):
    requirement = await get_project_entity(
        "requirements", requirement_id, user, "requirement.update"
    )
    if requirement["current_version_id"] != payload.expected_current_version_id:
        raise HTTPException(
            status_code=409,
            detail={"code": "REVISION_CONFLICT", "current_version_id": requirement["current_version_id"]},
        )
    await validate_requirement_sources(requirement["project_id"], payload.source_refs)
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
        "tags": payload.tags,
        "owner_id": payload.owner_id or requirement.get("owner_id"),
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
    try:
        await persist_acceptance_criteria(version, payload.acceptance_criteria)
    except Exception:
        await database.value.acceptance_criteria.delete_many({"requirement_version_id": version["_id"]})
        await database.value.requirement_versions.delete_one({"_id": version["_id"], "project_id": requirement["project_id"]})
        raise
    await index_requirement(version)
    await database.value.requirements.update_one(
        {"_id": requirement_id},
        {"$set": {"current_version_id": version["_id"], "status": "CHANGED", "tags": payload.tags, "owner_id": payload.owner_id or requirement.get("owner_id"), "updated_at": timestamp}},
    )
    await audit(user.id, "requirement_version_created", "RequirementVersion", version["_id"], requirement["project_id"], {"parent_version_id": parent["_id"]})
    return envelope(version, revision=1)


@router.get("/requirements/{requirement_id}/versions")
async def list_requirement_versions(requirement_id: str, user: CurrentUser = Depends(get_current_user)):
    requirement = await get_project_entity(
        "requirements", requirement_id, user, "requirement.version.read"
    )
    versions = await database.value.requirement_versions.find({"requirement_id": requirement_id}).sort("version", -1).to_list(500)
    return envelope(versions)


@router.post("/projects/{project_id}/requirements/{requirement_id}/submit-review")
async def submit_requirement_review(
    project_id: str,
    requirement_id: str,
    payload: ReviewTransitionInput,
    user: CurrentUser = Depends(get_current_user),
):
    requirement = await get_project_entity(
        "requirements", requirement_id, user, "requirement.submit_review"
    )
    if requirement["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    version = await database.value.requirement_versions.find_one(
        {"_id": requirement["current_version_id"], "project_id": project_id}
    )
    if version["status"] == "IN_REVIEW":
        return envelope(version, revision=version["revision"])
    if version["status"] != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    if version["revision"] != payload.expected_revision:
        raise HTTPException(
            status_code=409,
            detail={"code": "REVISION_CONFLICT", "current_revision": version["revision"]},
        )
    findings = requirement_findings(version)
    if any(item["severity"] == "error" for item in findings):
        raise HTTPException(
            status_code=409,
            detail={"code": "REQUIREMENT_LINT_BLOCKED", "findings": findings},
        )
    timestamp = now()
    result = await database.value.requirement_versions.update_one(
        {"_id": version["_id"], "project_id": project_id, "revision": payload.expected_revision, "status": "DRAFT"},
        {
            "$set": {
                "status": "IN_REVIEW",
                "review_note": payload.review_note,
                "review_submitted_by": user.id,
                "review_submitted_at": timestamp,
                "updated_at": timestamp,
            },
            "$inc": {"revision": 1},
        },
    )
    if result.matched_count != 1:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await database.value.requirements.update_one(
        {"_id": requirement_id, "project_id": project_id},
        {"$set": {"status": "IN_REVIEW", "updated_at": timestamp}},
    )
    version = await database.value.requirement_versions.find_one({"_id": version["_id"], "project_id": project_id})
    await audit(user.id, "requirement_review_submitted", "RequirementVersion", version["_id"], project_id, {"review_note": payload.review_note})
    return envelope(version, revision=version["revision"])


@router.post("/requirements/{requirement_id}/review")
async def submit_requirement_review_alias(
    requirement_id: str,
    payload: ReviewTransitionInput,
    user: CurrentUser = Depends(get_current_user),
):
    requirement = await get_project_entity("requirements", requirement_id, user, "requirement.submit_review")
    return await submit_requirement_review(requirement["project_id"], requirement_id, payload, user)


@router.post("/projects/{project_id}/requirements/{requirement_id}/request-changes")
async def request_requirement_changes(
    project_id: str,
    requirement_id: str,
    payload: ReviewTransitionInput,
    user: CurrentUser = Depends(get_current_user),
):
    requirement = await get_project_entity(
        "requirements", requirement_id, user, "requirement.approve"
    )
    if requirement["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    version = await database.value.requirement_versions.find_one(
        {"_id": requirement["current_version_id"], "project_id": project_id}
    )
    if version["status"] != "IN_REVIEW":
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    if version["revision"] != payload.expected_revision:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT", "current_revision": version["revision"]})
    timestamp = now()
    result = await database.value.requirement_versions.update_one(
        {"_id": version["_id"], "project_id": project_id, "revision": payload.expected_revision, "status": "IN_REVIEW"},
        {
            "$set": {
                "status": "DRAFT",
                "review_note": payload.review_note,
                "changes_requested_by": user.id,
                "changes_requested_at": timestamp,
                "updated_at": timestamp,
            },
            "$inc": {"revision": 1},
        },
    )
    if result.matched_count != 1:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await database.value.requirements.update_one(
        {"_id": requirement_id, "project_id": project_id},
        {"$set": {"status": "DRAFT", "updated_at": timestamp}},
    )
    version = await database.value.requirement_versions.find_one({"_id": version["_id"], "project_id": project_id})
    await audit(user.id, "requirement_changes_requested", "RequirementVersion", version["_id"], project_id, {"review_note": payload.review_note})
    return envelope(version, revision=version["revision"])


@router.post("/requirement-versions/{version_id}/baseline")
async def baseline_requirement_version(
    version_id: str,
    payload: RequirementBaselineInput,
    user: CurrentUser = Depends(get_current_user),
):
    version = await get_project_entity(
        "requirement_versions", version_id, user, "requirement.approve"
    )
    if version["status"] == "BASELINED":
        return envelope(version, revision=version["revision"])
    if version["status"] != "IN_REVIEW":
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    if version["revision"] != payload.expected_revision:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT", "current_revision": version["revision"]})
    findings = requirement_findings(version)
    if any(item["severity"] == "error" for item in findings):
        raise HTTPException(status_code=409, detail={"code": "REQUIREMENT_LINT_BLOCKED", "findings": findings})
    timestamp = now()
    version = await database.value.requirement_versions.find_one_and_update(
        {"_id": version_id, "project_id": version["project_id"], "status": "IN_REVIEW", "revision": payload.expected_revision},
        {"$set": {"status": "BASELINED", "review_note": payload.review_note, "baselined_at": timestamp, "baselined_by": user.id, "updated_at": timestamp}, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not version:
        current = await database.value.requirement_versions.find_one({"_id": version_id})
        if current and current.get("status") == "BASELINED":
            return envelope(current, revision=current["revision"])
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await database.value.requirements.update_one(
        {"_id": version["requirement_id"]},
        {"$set": {"current_version_id": version_id, "status": "BASELINED", "updated_at": timestamp}},
    )
    await database.value.acceptance_criteria.update_many(
        {"requirement_version_id": version_id, "status": "draft"},
        {"$set": {"status": "approved", "approved_at": timestamp, "approved_by": user.id}},
    )
    indexed = await index_requirement(version)
    version = await database.value.requirement_versions.find_one({"_id": version_id})
    await audit(user.id, "requirement_version_baselined", "RequirementVersion", version_id, version["project_id"])
    return envelope(version, revision=version["revision"], status="DEGRADED" if not indexed else "SUCCESS", degraded_mode="DEGRADED_VECTOR" if not indexed else None)


@router.post("/projects/{project_id}/requirements/{requirement_id}/approve")
async def approve_requirement(
    project_id: str,
    requirement_id: str,
    payload: RequirementBaselineInput,
    user: CurrentUser = Depends(get_current_user),
):
    requirement = await get_project_entity(
        "requirements", requirement_id, user, "requirement.approve"
    )
    if requirement["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    return await baseline_requirement_version(
        requirement["current_version_id"],
        payload,
        user,
    )


@router.post("/requirements/{requirement_id}/approve")
async def approve_requirement_alias(
    requirement_id: str,
    payload: RequirementBaselineInput,
    user: CurrentUser = Depends(get_current_user),
):
    requirement = await get_project_entity("requirements", requirement_id, user, "requirement.approve")
    return await baseline_requirement_version(requirement["current_version_id"], payload, user)


@router.post("/requirements/{requirement_id}/obsolete")
async def mark_requirement_obsolete(
    requirement_id: str,
    payload: RequirementObsoleteInput,
    user: CurrentUser = Depends(get_current_user),
):
    requirement = await get_project_entity(
        "requirements", requirement_id, user, "requirement.archive"
    )
    if requirement.get("status") == "OBSOLETE":
        return envelope(requirement)
    if requirement.get("current_version_id") != payload.expected_current_version_id:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "REVISION_CONFLICT",
                "current_version_id": requirement.get("current_version_id"),
            },
        )
    timestamp = now()
    updated = await database.value.requirements.find_one_and_update(
        {
            "_id": requirement_id,
            "project_id": requirement["project_id"],
            "current_version_id": payload.expected_current_version_id,
            "status": requirement["status"],
        },
        {
            "$set": {
                "status": "OBSOLETE",
                "obsolete_reason": payload.reason,
                "obsolete_by": user.id,
                "obsolete_at": timestamp,
                "updated_at": timestamp,
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    version_update = await database.value.requirement_versions.update_one(
        {
            "_id": payload.expected_current_version_id,
            "project_id": requirement["project_id"],
            "requirement_id": requirement_id,
            "status": {"$in": ["DRAFT", "IN_REVIEW", "BASELINED"]},
        },
        {
            "$set": {
                "status": "OBSOLETE",
                "obsolete_reason": payload.reason,
                "obsolete_by": user.id,
                "obsolete_at": timestamp,
                "updated_at": timestamp,
            },
            "$inc": {"revision": 1},
        },
    )
    if version_update.matched_count != 1:
        await database.value.requirements.update_one(
            {
                "_id": requirement_id,
                "project_id": requirement["project_id"],
                "status": "OBSOLETE",
                "obsolete_at": timestamp,
            },
            {
                "$set": {"status": requirement["status"], "updated_at": now()},
                "$unset": {
                    "obsolete_reason": "",
                    "obsolete_by": "",
                    "obsolete_at": "",
                },
            },
        )
        raise HTTPException(status_code=409, detail={"code": "REQUIREMENT_VERSION_CONFLICT"})
    await audit(
        user.id,
        "requirement_marked_obsolete",
        "Requirement",
        requirement_id,
        requirement["project_id"],
        {"reason": payload.reason, "version_id": payload.expected_current_version_id},
    )
    current_version = await database.value.requirement_versions.find_one(
        {"_id": payload.expected_current_version_id, "project_id": requirement["project_id"]}
    )
    return envelope({**updated, "current_version": current_version})


@router.post("/requirement-versions/{version_id}/ai/lint")
async def lint_requirement(version_id: str, user: CurrentUser = Depends(get_current_user)):
    version = await get_project_entity(
        "requirement_versions", version_id, user, "ai.run_lint"
    )
    findings = requirement_findings(version)
    result = {
        "requirement_version_id": version_id,
        "findings": findings,
        "valid": not any(item["severity"] == "error" for item in findings),
        "model": {"provider": "rules", "model": "requirement-linter-v1", "prompt_version": "qa-v1", "tool_schema_version": "1"},
    }
    await database.value.ai_findings.insert_one({"_id": new_id("AIF"), "project_id": version["project_id"], "artifact_type": "requirement_version", "artifact_id": version_id, **result, "created_at": now()})
    return envelope(result)


@router.post("/projects/{project_id}/requirements/{requirement_id}/lint")
async def lint_requirement_draft(project_id: str, requirement_id: str, user: CurrentUser = Depends(get_current_user)):
    requirement = await get_project_entity("requirements", requirement_id, user, "ai.run_lint")
    if requirement["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    return await lint_requirement(requirement["current_version_id"], user)


@router.post("/requirements/{requirement_id}/lint")
async def lint_requirement_alias(requirement_id: str, user: CurrentUser = Depends(get_current_user)):
    requirement = await get_project_entity("requirements", requirement_id, user, "ai.run_lint")
    return await lint_requirement(requirement["current_version_id"], user)


@router.post("/requirements/{requirement_id}/compare")
async def compare_requirement(
    requirement_id: str,
    payload: RequirementCompareInput,
    user: CurrentUser = Depends(get_current_user),
):
    requirement = await get_project_entity(
        "requirements", requirement_id, user, "requirement.version.read"
    )
    versions = await database.value.requirement_versions.find(
        {"requirement_id": requirement_id, "_id": {"$in": [payload.from_version_id, payload.to_version_id]}}
    ).to_list(2)
    by_id = {item["_id"]: item for item in versions}
    if set(by_id) != {payload.from_version_id, payload.to_version_id}:
        raise HTTPException(status_code=404, detail="Không tìm thấy đủ hai phiên bản")
    changes = semantic_changes(by_id[payload.from_version_id], by_id[payload.to_version_id])
    return envelope({"from_version": by_id[payload.from_version_id], "to_version": by_id[payload.to_version_id], "changes": changes})


@router.get("/requirements/{requirement_id}/diff")
async def diff_requirement(
    requirement_id: str,
    from_version: str = Query(alias="from", min_length=1, max_length=200),
    to_version: str = Query(alias="to", min_length=1, max_length=200),
    user: CurrentUser = Depends(get_current_user),
):
    return await compare_requirement(
        requirement_id,
        RequirementCompareInput(from_version_id=from_version, to_version_id=to_version),
        user,
    )


@router.post("/projects/{project_id}/requirement-documents", status_code=201)
async def create_requirement_document(
    project_id: str,
    payload: ImportCreate,
    user: CurrentUser = Depends(get_current_user),
):
    document = await create_requirement_document_record(project_id, payload, user)
    return envelope(document, revision=document["revision"])


@router.post("/projects/{project_id}/requirement-documents/upload", status_code=201)
async def upload_requirement_document(
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
    await get_project(project_id, user, "requirement.create")
    filename = file.filename or f"requirements.{format}"
    content_hash = hashlib.sha256(data).hexdigest()
    existing = await database.value.requirement_documents.find_one(
        {"project_id": project_id, "content_hash": content_hash}
    )
    if existing:
        return envelope(existing, revision=existing["revision"])
    document_id = new_id("RDOC")
    source = await store_raw_requirement_source(project_id, document_id, filename, file.content_type, data)
    timestamp = now()
    document = {
        "_id": document_id,
        "project_id": project_id,
        "filename": filename,
        "format": format,
        "content_hash": source["sha256"],
        "raw_source": source,
        "normalized_content": None,
        "status": "UPLOADED",
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await database.value.requirement_documents.insert_one(document)
    except DuplicateKeyError:
        existing = await database.value.requirement_documents.find_one(
            {"project_id": project_id, "content_hash": content_hash}
        )
        if existing:
            return envelope(existing, revision=existing["revision"])
        raise
    await audit(user.id, "requirement_document_uploaded", "RequirementDocument", document_id, project_id, {"content_hash": source["sha256"], "object_key": source["object_key"], "format": format})
    try:
        content = extract_file_content(data, format)
    except Exception as error:
        await database.value.requirement_documents.update_one(
            {"_id": document_id, "project_id": project_id},
            {"$set": {"status": "PARSE_FAILED", "parse_error_type": type(error).__name__, "updated_at": now()}, "$inc": {"revision": 1}},
        )
        document = await database.value.requirement_documents.find_one({"_id": document_id, "project_id": project_id})
        await audit(user.id, "requirement_document_parse_failed", "RequirementDocument", document_id, project_id, {"error_type": type(error).__name__})
        return envelope(document, revision=document["revision"], status="DEGRADED", degraded_mode="PARSER_FAILED")
    normalized = serialized_content(content)
    await database.value.requirement_documents.update_one(
        {"_id": document_id, "project_id": project_id},
        {"$set": {"normalized_content": content, "normalized_content_hash": hashlib.sha256(normalized.encode("utf-8")).hexdigest(), "status": "READY", "updated_at": now()}, "$inc": {"revision": 1}},
    )
    document = await database.value.requirement_documents.find_one({"_id": document_id, "project_id": project_id})
    return envelope(document, revision=document["revision"])


@router.get("/requirement-documents/{document_id}")
async def get_requirement_document(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    document = await get_project_entity(
        "requirement_documents", document_id, user, "requirement.read"
    )
    return envelope(document, revision=document["revision"])


@router.post("/requirement-documents/{document_id}/retry-parse")
async def retry_requirement_document_parse(
    document_id: str,
    payload: RequirementParseRetry,
    user: CurrentUser = Depends(get_current_user),
):
    document = await get_project_entity(
        "requirement_documents", document_id, user, "requirement.create"
    )
    if document.get("status") == "READY":
        return envelope(document, revision=document["revision"])
    if document.get("status") != "PARSE_FAILED":
        raise HTTPException(
            status_code=409,
            detail={"code": "DOCUMENT_NOT_RETRYABLE", "status": document.get("status")},
        )
    claimed = await database.value.requirement_documents.update_one(
        {
            "_id": document_id,
            "project_id": document["project_id"],
            "status": "PARSE_FAILED",
            "revision": payload.expected_revision,
        },
        {
            "$set": {"status": "PARSING", "updated_at": now()},
            "$inc": {"revision": 1},
        },
    )
    if claimed.matched_count != 1:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    try:
        data = await read_raw_requirement_source(document)
        content = extract_file_content(data, document["format"])
    except Exception as error:
        await database.value.requirement_documents.update_one(
            {"_id": document_id, "project_id": document["project_id"], "status": "PARSING"},
            {
                "$set": {
                    "status": "PARSE_FAILED",
                    "parse_error_type": type(error).__name__,
                    "updated_at": now(),
                },
                "$inc": {"revision": 1},
            },
        )
        failed = await database.value.requirement_documents.find_one(
            {"_id": document_id, "project_id": document["project_id"]}
        )
        await audit(
            user.id,
            "requirement_document_parse_retry_failed",
            "RequirementDocument",
            document_id,
            document["project_id"],
            {"error_type": type(error).__name__},
        )
        return envelope(
            failed,
            revision=failed["revision"],
            status="DEGRADED",
            degraded_mode="PARSER_FAILED",
        )
    normalized = serialized_content(content)
    updated = await database.value.requirement_documents.find_one_and_update(
        {"_id": document_id, "project_id": document["project_id"], "status": "PARSING"},
        {
            "$set": {
                "normalized_content": content,
                "normalized_content_hash": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
                "status": "READY",
                "parse_error_type": None,
                "updated_at": now(),
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "PARSE_RETRY_CONFLICT"})
    await audit(
        user.id,
        "requirement_document_parse_retry_succeeded",
        "RequirementDocument",
        document_id,
        document["project_id"],
    )
    return envelope(updated, revision=updated["revision"])


@router.post("/requirement-documents/{document_id}/extract", status_code=201)
async def extract_requirement_document(
    document_id: str,
    payload: RequirementExtractionInput,
    user: CurrentUser = Depends(get_current_user),
):
    document = await get_project_entity(
        "requirement_documents", document_id, user, "requirement.create"
    )
    if document.get("normalized_content") is None:
        raise HTTPException(status_code=409, detail={"code": "DOCUMENT_PARSE_REQUIRED", "status": document.get("status")})
    existing = await database.value.import_jobs.find_one({"source_document_id": document_id})
    if existing:
        return envelope(existing, revision=existing.get("revision", 1))
    await audit(
        user.id,
        "requirement_extraction_requested",
        "RequirementDocument",
        document_id,
        document["project_id"],
    )
    candidates = atomic_requirement_candidates(document)
    job = {
        "_id": new_id("RIMP"),
        "project_id": document["project_id"],
        "source_document_id": document_id,
        "source_content_hash": document["content_hash"],
        "filename": document["filename"],
        "format": document["format"],
        "status": "PREVIEW_READY",
        "preview": candidates,
        "candidate_count": len(candidates),
        "extraction_mode": "DETERMINISTIC",
        "idempotency_key": payload.idempotency_key,
        "revision": 1,
        "created_by": user.id,
        "created_at": now(),
    }
    try:
        await database.value.import_jobs.insert_one(job)
    except DuplicateKeyError:
        existing = await database.value.import_jobs.find_one({"source_document_id": document_id})
        return envelope(existing, revision=existing.get("revision", 1))
    await database.value.requirement_documents.update_one(
        {"_id": document_id, "project_id": document["project_id"]},
        {
            "$set": {
                "status": "EXTRACTED",
                "last_import_job_id": job["_id"],
                "updated_at": now(),
            },
            "$inc": {"revision": 1},
        },
    )
    await audit(
        user.id,
        "requirement_extraction_completed",
        "RequirementDocument",
        document_id,
        document["project_id"],
        {"job_id": job["_id"], "candidate_count": len(candidates)},
    )
    return envelope(job, revision=1)


@router.post("/projects/{project_id}/requirement-imports", status_code=201)
async def create_requirement_import(
    project_id: str,
    payload: ImportCreate,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "requirement.create")
    previews = parse_import(payload)
    job = {
        "_id": new_id("RIMP"),
        "project_id": project_id,
        "filename": payload.filename,
        "format": payload.format,
        "status": "PREVIEW_READY",
        "preview": previews,
        "candidate_count": len(previews),
        "revision": 1,
        "created_by": user.id,
        "created_at": now(),
    }
    await database.value.import_jobs.insert_one(job)
    await audit(user.id, "requirement_import_previewed", "RequirementImport", job["_id"], project_id, {"count": len(previews)})
    return envelope(job, revision=1)


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
    job = await get_project_entity("import_jobs", job_id, user, "requirement.read")
    return envelope(job, revision=job.get("revision", 1))


@router.patch("/requirement-imports/{job_id}")
async def review_requirement_import(
    job_id: str,
    payload: RequirementImportReview,
    user: CurrentUser = Depends(get_current_user),
):
    job = await get_project_entity("import_jobs", job_id, user, "requirement.create")
    if job.get("status") != "PREVIEW_READY":
        raise HTTPException(
            status_code=409,
            detail={"code": "IMPORT_PREVIEW_NOT_EDITABLE", "status": job.get("status")},
        )
    preview = [candidate.model_dump() for candidate in payload.preview]
    for candidate in preview:
        validate_doc(candidate["content_doc"])
        for criterion in candidate.get("acceptance_criteria", []):
            validate_doc(criterion["content_doc"])
    updated = await database.value.import_jobs.find_one_and_update(
        {
            "_id": job_id,
            "project_id": job["project_id"],
            "status": "PREVIEW_READY",
            "revision": payload.expected_revision,
        },
        {
            "$set": {
                "preview": preview,
                "candidate_count": len(preview),
                "review_note": payload.review_note,
                "reviewed_by": user.id,
                "reviewed_at": now(),
                "updated_at": now(),
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "requirement_import_reviewed",
        "RequirementImport",
        job_id,
        job["project_id"],
        {"candidate_count": len(preview), "review_note": payload.review_note},
    )
    return envelope(updated, revision=updated["revision"])


@router.post("/requirement-imports/{job_id}/confirm")
async def confirm_requirement_import(
    job_id: str,
    payload: ImportConfirm,
    user: CurrentUser = Depends(get_current_user),
):
    job = await get_project_entity(
        "import_jobs", job_id, user, "requirement.create"
    )
    if job["status"] == "CONFIRMED":
        return envelope(job)
    indexes = payload.selected_indexes or list(range(len(job["preview"])))
    indexes = list(dict.fromkeys(indexes))
    for index in indexes:
        if index < 0 or index >= len(job["preview"]):
            raise HTTPException(status_code=422, detail="Chỉ mục preview không hợp lệ")
    claim_filter = {
        "_id": job_id,
        "project_id": job["project_id"],
        "status": "PREVIEW_READY",
    }
    if payload.expected_revision is not None:
        claim_filter["revision"] = payload.expected_revision
    claimed = await database.value.import_jobs.update_one(
        claim_filter,
        {
            "$set": {"status": "CONFIRMING", "confirming_by": user.id, "updated_at": now()},
            "$inc": {"revision": 1},
        },
    )
    if claimed.matched_count != 1:
        current = await database.value.import_jobs.find_one(
            {"_id": job_id, "project_id": job["project_id"]}
        )
        if current and current.get("status") == "CONFIRMED":
            return envelope(current)
        raise HTTPException(status_code=409, detail={"code": "IMPORT_CONFIRM_IN_PROGRESS"})
    created = []
    try:
        for index in indexes:
            item = job["preview"][index]
            created.append(
                await create_requirement_record(
                    job["project_id"],
                    RequirementCreate(**item),
                    user,
                    origin="import",
                )
            )
    except Exception:
        requirement_ids = [item["_id"] for item in created]
        version_ids = [item["current_version"]["_id"] for item in created]
        if requirement_ids:
            await database.value.acceptance_criteria.delete_many(
                {"requirement_version_id": {"$in": version_ids}}
            )
            await database.value.requirement_versions.delete_many({"_id": {"$in": version_ids}})
            await database.value.requirements.delete_many({"_id": {"$in": requirement_ids}})
        await database.value.import_jobs.update_one(
            {"_id": job_id, "project_id": job["project_id"], "status": "CONFIRMING"},
            {"$set": {"status": "PREVIEW_READY", "updated_at": now()}, "$inc": {"revision": 1}},
        )
        await audit(
            user.id,
            "requirement_import_confirmation_failed",
            "RequirementImport",
            job_id,
            job["project_id"],
        )
        raise
    await database.value.import_jobs.update_one(
        {"_id": job_id, "project_id": job["project_id"], "status": "CONFIRMING"},
        {"$set": {"status": "CONFIRMED", "created_requirement_ids": [item["_id"] for item in created], "selected_indexes": indexes, "rejected_indexes": [index for index in range(len(job["preview"])) if index not in indexes], "confirmed_at": now(), "confirmed_by": user.id, "updated_at": now()}, "$inc": {"revision": 1}},
    )
    if job.get("source_document_id"):
        await database.value.requirement_documents.update_one(
            {"_id": job["source_document_id"], "project_id": job["project_id"]},
            {"$set": {"status": "CONFIRMED", "updated_at": now()}, "$inc": {"revision": 1}},
        )
    await audit(
        user.id,
        "requirement_import_confirmed",
        "RequirementImport",
        job_id,
        job["project_id"],
        {
            "created_requirement_ids": [item["_id"] for item in created],
            "selected_indexes": indexes,
            "rejected_indexes": [
                index for index in range(len(job["preview"])) if index not in indexes
            ],
        },
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


def atomic_requirement_candidates(document):
    content = document["normalized_content"]
    if document["format"] in {"csv", "xlsx", "openapi", "postman"}:
        candidates = parse_import(
            ImportCreate(
                filename=document["filename"],
                format=document["format"],
                content=content,
            )
        )
        for index, candidate in enumerate(candidates):
            candidate["source_refs"] = [
                {
                    "requirement_document_id": document["_id"],
                    "content_hash": document["content_hash"],
                    "candidate_index": index,
                    "format": document["format"],
                }
            ]
            candidate["extraction_confidence"] = 1.0
        return candidates
    text = str(content).replace("\r\n", "\n").replace("\r", "\n")
    matches = list(re.finditer(r"[^\n]+?(?:[.!?;]+(?=\s|$)|(?=\n)|$)", text))
    candidates = []
    for match in matches:
        raw = match.group(0)
        value = re.sub(r"^\s*(?:[-*•]+|\d+[.)])\s*", "", raw).strip()
        if len(value) < 2:
            continue
        source_start = match.start() + raw.find(value)
        source_end = source_start + len(value)
        candidate = {
            "title": value[:300],
            "content_doc": text_doc(value),
            "acceptance_criteria": [],
            "source_refs": [
                {
                    "requirement_document_id": document["_id"],
                    "content_hash": document["content_hash"],
                    "source_start": source_start,
                    "source_end": source_end,
                    "source_text_hash": hashlib.sha256(value.encode("utf-8")).hexdigest(),
                    "format": document["format"],
                }
            ],
            "extraction_confidence": 0.8,
        }
        candidates.append(candidate)
        if len(candidates) == 500:
            break
    return candidates


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


async def validate_requirement_sources(project_id, source_refs):
    references = [item for item in source_refs or [] if item.get("requirement_document_id")]
    if not references:
        return
    document_ids = list(dict.fromkeys(item["requirement_document_id"] for item in references))
    documents = await database.value.requirement_documents.find({"project_id": project_id, "_id": {"$in": document_ids}}).to_list(len(document_ids))
    by_id = {item["_id"]: item for item in documents}
    if set(by_id) != set(document_ids):
        raise HTTPException(status_code=422, detail={"code": "CROSS_PROJECT_OR_MISSING_REQUIREMENT_DOCUMENT"})
    for reference in references:
        expected_hash = reference.get("content_hash")
        if expected_hash and expected_hash != by_id[reference["requirement_document_id"]].get("content_hash"):
            raise HTTPException(status_code=422, detail={"code": "REQUIREMENT_SOURCE_HASH_MISMATCH"})


async def index_requirement(version):
    indexed = await index_artifact(version["project_id"], "requirement_version", version["requirement_id"], version["_id"], version["title"], version.get("plain_text_projection", ""), version.get("status", "DRAFT"), "baseline" if version.get("status") == "BASELINED" else "draft", version.get("version"))
    await database.value.requirement_versions.update_one({"_id": version["_id"]}, {"$set": {"index_status": "READY" if indexed else "FAILED", "index_error_code": None if indexed else "KNOWLEDGE_INDEX_FAILED", "updated_at": now()}})
    return indexed
