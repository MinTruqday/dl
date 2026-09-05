import csv
import hashlib
import io
import json
import re
import zipfile
from xml.etree import ElementTree

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
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
    require_action_policy,
    sort_spec,
    validate_doc,
)
from src.core.database import database
from src.core.configuration import settings
from src.domain.schemas import (
    ImportConfirm,
    ImportCreate,
    KnowledgeSourceCreate,
    ProjectArchiveInput,
    RequirementBaselineInput,
    RequirementCandidateMergeInput,
    RequirementCandidateRejectInput,
    RequirementCandidateSplitInput,
    RequirementCompareInput,
    RequirementDependencyInput,
    RequirementDuplicateCheckInput,
    RequirementDocumentPatch,
    RequirementCreate,
    RequirementDraftPatch,
    RequirementExtractionInput,
    RequirementImportReview,
    RequirementObsoleteInput,
    RequirementMergeInput,
    RequirementRestoreInput,
    RequirementSplitInput,
    RequirementParseRetry,
    RequirementVersionCreate,
    ReviewTransitionInput,
)
from src.services.change_analysis import semantic_changes
from src.services.linters import requirement_duplicate_score, requirement_findings
from src.services.project_knowledge import index_artifact


router = APIRouter(prefix="/kiem-thu", tags=["Yêu cầu kiểm thử"])


def serialized_content(content):
    if isinstance(content, str):
        return content
    return json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def prepare_requirement_candidates(job_id, candidates):
    prepared = []
    for index, value in enumerate(candidates):
        candidate = dict(value)
        candidate["candidate_id"] = candidate.get("candidate_id") or f"{job_id}-CAND-{index + 1}"
        candidate["candidate_status"] = "ACTIVE"
        candidate["candidate_revision"] = int(candidate.get("candidate_revision", 1))
        candidate["parent_candidate_ids"] = list(candidate.get("parent_candidate_ids", []))
        prepared.append(candidate)
    return prepared


def candidate_fingerprint(candidate):
    return hashlib.sha256(
        serialized_content(
            {
                "candidate_id": candidate.get("candidate_id"),
                "title": candidate.get("title"),
                "content_doc": candidate.get("content_doc"),
                "source_refs": candidate.get("source_refs", []),
            }
        ).encode("utf-8")
    ).hexdigest()


async def create_requirement_document_record(project_id, payload, user):
    await get_project(project_id, user, "requirement_document.upload")
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
        "source_version": 1,
        "source_type": "reference",
        "authority": "reference",
        "status": "READY",
        "index_status": "PENDING",
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
    indexed = await index_artifact(project_id, "requirement_document", document["_id"], document["_id"], document["filename"], content, document["status"], document["authority"], document["source_version"])
    document["index_status"] = "INDEXED" if indexed else "FAILED"
    document["indexed_at"] = now()
    await database.value.requirement_documents.update_one({"_id": document["_id"], "project_id": project_id}, {"$set": {"index_status": document["index_status"], "indexed_at": document["indexed_at"]}})
    return document


async def store_raw_requirement_source(project_id, document_id, filename, content_type, data):
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{settings.CLOUD_URL.rstrip('/')}/noi-bo/kiem-thu/nguon-yeu-cau",
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
            f"{settings.CLOUD_URL.rstrip('/')}/noi-bo/kiem-thu/nguon-yeu-cau",
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


def unique_source_refs(values):
    result = []
    seen = set()
    for value in values:
        marker = serialized_content(value)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(value)
    return result


async def load_requirement_baselines(project_id, requirement_ids, expected_version_ids, user, permission):
    await get_project(project_id, user, permission)
    ordered_ids = list(dict.fromkeys(requirement_ids))
    if len(ordered_ids) != len(requirement_ids):
        raise HTTPException(status_code=422, detail={"code": "DUPLICATE_SOURCE_REQUIREMENT"})
    if set(expected_version_ids) != set(ordered_ids):
        raise HTTPException(status_code=422, detail={"code": "SOURCE_VERSION_SET_MISMATCH"})
    requirements = await database.value.requirements.find(
        {"_id": {"$in": ordered_ids}, "project_id": project_id}
    ).to_list(len(ordered_ids))
    by_id = {item["_id"]: item for item in requirements}
    if set(by_id) != set(ordered_ids):
        raise HTTPException(status_code=404, detail={"code": "SOURCE_REQUIREMENT_NOT_FOUND"})
    version_ids = list(expected_version_ids.values())
    versions = await database.value.requirement_versions.find(
        {"_id": {"$in": version_ids}, "project_id": project_id}
    ).to_list(len(version_ids))
    versions_by_id = {item["_id"]: item for item in versions}
    if set(versions_by_id) != set(version_ids):
        raise HTTPException(status_code=404, detail={"code": "SOURCE_REQUIREMENT_VERSION_NOT_FOUND"})
    sources = []
    for requirement_id in ordered_ids:
        requirement = by_id[requirement_id]
        version_id = expected_version_ids[requirement_id]
        version = versions_by_id[version_id]
        if requirement.get("current_version_id") != version_id:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "STALE_SOURCE_REQUIREMENT",
                    "requirement_id": requirement_id,
                    "current_version_id": requirement.get("current_version_id"),
                },
            )
        if requirement.get("status") != "BASELINED" or version.get("status") != "BASELINED":
            raise HTTPException(
                status_code=409,
                detail={"code": "SOURCE_REQUIREMENT_NOT_BASELINED", "requirement_id": requirement_id},
            )
        sources.append((requirement, version))
    return sources


async def claim_requirement_transformation(project_id, transformation_type, payload, source_requirement_ids, source_version_ids, user):
    request_payload = payload.model_dump(mode="json")
    request_fingerprint = hashlib.sha256(
        serialized_content({key: value for key, value in request_payload.items() if key != "idempotency_key"}).encode("utf-8")
    ).hexdigest()
    existing = await database.value.requirement_transformations.find_one(
        {"project_id": project_id, "idempotency_key": payload.idempotency_key}
    )
    if existing:
        if existing.get("request_fingerprint") != request_fingerprint:
            raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
        if existing.get("status") == "CONFIRMED":
            return existing, False
        if existing.get("status") == "CONFIRMING":
            raise HTTPException(status_code=409, detail={"code": "REQUIREMENT_TRANSFORMATION_IN_PROGRESS"})
        claimed = await database.value.requirement_transformations.find_one_and_update(
            {"_id": existing["_id"], "project_id": project_id, "status": "FAILED"},
            {
                "$set": {"status": "CONFIRMING", "updated_at": now()},
                "$unset": {"error_code": ""},
                "$inc": {"attempt": 1},
            },
            return_document=ReturnDocument.AFTER,
        )
        if not claimed:
            raise HTTPException(status_code=409, detail={"code": "REQUIREMENT_TRANSFORMATION_CONFLICT"})
        return claimed, True
    timestamp = now()
    transformation = {
        "_id": new_id("RTX"),
        "project_id": project_id,
        "type": transformation_type,
        "source_requirement_ids": source_requirement_ids,
        "source_version_ids": source_version_ids,
        "result_requirement_ids": [],
        "result_version_ids": [],
        "reason": payload.reason,
        "idempotency_key": payload.idempotency_key,
        "request_fingerprint": request_fingerprint,
        "status": "CONFIRMING",
        "attempt": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await database.value.requirement_transformations.insert_one(transformation)
    except DuplicateKeyError:
        existing = await database.value.requirement_transformations.find_one(
            {"project_id": project_id, "idempotency_key": payload.idempotency_key}
        )
        if existing and existing.get("request_fingerprint") == request_fingerprint and existing.get("status") == "CONFIRMED":
            return existing, False
        raise HTTPException(status_code=409, detail={"code": "REQUIREMENT_TRANSFORMATION_CONFLICT"})
    return transformation, True


async def prepare_requirement_output(project_id, draft, user, transformation, index, sources, relation):
    validate_doc(draft.content_doc)
    keys = [item.key for item in draft.acceptance_criteria]
    if len(keys) != len(set(keys)):
        raise HTTPException(status_code=422, detail={"code": "DUPLICATE_ACCEPTANCE_CRITERION_KEY"})
    for item in draft.acceptance_criteria:
        validate_doc(item.content_doc)
    source_refs = unique_source_refs(
        list(draft.source_refs)
        + [
            {
                "type": "requirement_version",
                "requirement_id": requirement["_id"],
                "requirement_version_id": version["_id"],
                "relation": relation,
            }
            for requirement, version in sources
        ]
    )
    await validate_requirement_sources(project_id, source_refs)
    timestamp = now()
    requirement_id = f"{transformation['_id']}-REQ-{index + 1}"
    version_id = f"{transformation['_id']}-REQV-{index + 1}"
    requirement_key = draft.requirement_key or await next_key(project_id, "requirement", "REQ")
    version = {
        "_id": version_id,
        "project_id": project_id,
        "requirement_id": requirement_id,
        "requirement_key": requirement_key,
        "version": 1,
        "title": draft.title,
        "type": draft.type,
        "priority": draft.priority,
        "risk": draft.risk,
        "content_doc": draft.content_doc,
        "plain_text_projection": plain_text(draft.content_doc),
        "business_rules": draft.business_rules,
        "actors": draft.actors,
        "dependencies": draft.dependencies,
        "source_refs": source_refs,
        "tags": draft.tags,
        "owner_id": draft.owner_id or user.id,
        "acceptance_criterion_ids": [],
        "parent_version_id": None,
        "change_reason": transformation["reason"],
        "status": "DRAFT",
        "revision": 1,
        "origin": relation,
        "transformation_id": transformation["_id"],
        "derived_from": [
            {"requirement_id": requirement["_id"], "requirement_version_id": source["_id"]}
            for requirement, source in sources
        ],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    criteria = []
    for criterion_index, value in enumerate(draft.acceptance_criteria):
        item = value.model_dump()
        item["status"] = "draft"
        criterion = {
            "_id": f"{transformation['_id']}-AC-{index + 1}-{criterion_index + 1}",
            "project_id": project_id,
            "requirement_version_id": version_id,
            **item,
            "plain_text": plain_text(item["content_doc"]),
            "created_at": timestamp,
        }
        criteria.append(criterion)
    version["acceptance_criterion_ids"] = [item["_id"] for item in criteria]
    requirement = {
        "_id": requirement_id,
        "project_id": project_id,
        "requirement_key": requirement_key,
        "current_version_id": version_id,
        "status": "DRAFT",
        "owner_id": draft.owner_id or user.id,
        "tags": draft.tags,
        "transformation_id": transformation["_id"],
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    return requirement, version, criteria


async def hydrate_requirement_transformation(transformation):
    requirements = await database.value.requirements.find(
        {"project_id": transformation["project_id"], "_id": {"$in": transformation.get("result_requirement_ids", [])}}
    ).to_list(100)
    versions = await database.value.requirement_versions.find(
        {"project_id": transformation["project_id"], "_id": {"$in": transformation.get("result_version_ids", [])}}
    ).to_list(100)
    versions_by_id = {item["_id"]: item for item in versions}
    return {
        "transformation": transformation,
        "requirements": [
            {**item, "current_version": versions_by_id.get(item.get("current_version_id"))}
            for item in requirements
        ],
    }


async def execute_requirement_transformation(project_id, transformation, sources, drafts, user, relation):
    output_requirements = []
    output_versions = []
    output_criteria = []
    updated_sources = []
    try:
        for index, draft in enumerate(drafts):
            requirement, version, criteria = await prepare_requirement_output(
                project_id, draft, user, transformation, index, sources, relation
            )
            output_requirements.append(requirement)
            output_versions.append(version)
            output_criteria.extend(criteria)
        keys = [item["requirement_key"] for item in output_requirements]
        if len(keys) != len(set(keys)):
            raise HTTPException(status_code=422, detail={"code": "DUPLICATE_OUTPUT_REQUIREMENT_KEY"})
        await database.value.requirements.insert_many(output_requirements)
        await database.value.requirement_versions.insert_many(output_versions)
        if output_criteria:
            await database.value.acceptance_criteria.insert_many(output_criteria)
        result_ids = [item["_id"] for item in output_requirements]
        for source_requirement, source_version in sources:
            version_result = await database.value.requirement_versions.update_one(
                {
                    "_id": source_version["_id"],
                    "project_id": project_id,
                    "status": "BASELINED",
                    "superseded_by_transformation_id": {"$exists": False},
                },
                {
                    "$set": {
                        "status": "SUPERSEDED",
                        "superseded_by_requirement_ids": result_ids,
                        "superseded_by_transformation_id": transformation["_id"],
                        "superseded_at": now(),
                        "superseded_by": user.id,
                        "updated_at": now(),
                    },
                    "$inc": {"revision": 1},
                },
            )
            if version_result.matched_count != 1:
                raise HTTPException(status_code=409, detail={"code": "STALE_SOURCE_REQUIREMENT"})
            updated_sources.append((source_requirement["_id"], source_version["_id"]))
            requirement_result = await database.value.requirements.update_one(
                {
                    "_id": source_requirement["_id"],
                    "project_id": project_id,
                    "current_version_id": source_version["_id"],
                    "status": "BASELINED",
                    "superseded_by_transformation_id": {"$exists": False},
                },
                {
                    "$set": {
                        "status": "SUPERSEDED",
                        "superseded_by_requirement_ids": result_ids,
                        "superseded_by_transformation_id": transformation["_id"],
                        "superseded_at": now(),
                        "superseded_by": user.id,
                        "updated_at": now(),
                    }
                },
            )
            if requirement_result.matched_count != 1:
                raise HTTPException(status_code=409, detail={"code": "STALE_SOURCE_REQUIREMENT"})
        transformation = await database.value.requirement_transformations.find_one_and_update(
            {"_id": transformation["_id"], "project_id": project_id, "status": "CONFIRMING"},
            {
                "$set": {
                    "status": "CONFIRMED",
                    "result_requirement_ids": result_ids,
                    "result_version_ids": [item["_id"] for item in output_versions],
                    "confirmed_at": now(),
                    "updated_at": now(),
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        if not transformation:
            raise HTTPException(status_code=409, detail={"code": "REQUIREMENT_TRANSFORMATION_CONFLICT"})
    except Exception as error:
        for requirement_id, version_id in updated_sources:
            await database.value.requirements.update_one(
                {"_id": requirement_id, "project_id": project_id, "superseded_by_transformation_id": transformation["_id"]},
                {
                    "$set": {"status": "BASELINED", "updated_at": now()},
                    "$unset": {
                        "superseded_by_requirement_ids": "",
                        "superseded_by_transformation_id": "",
                        "superseded_at": "",
                        "superseded_by": "",
                    },
                },
            )
            await database.value.requirement_versions.update_one(
                {"_id": version_id, "project_id": project_id, "superseded_by_transformation_id": transformation["_id"]},
                {
                    "$set": {"status": "BASELINED", "updated_at": now()},
                    "$unset": {
                        "superseded_by_requirement_ids": "",
                        "superseded_by_transformation_id": "",
                        "superseded_at": "",
                        "superseded_by": "",
                    },
                    "$inc": {"revision": 1},
                },
            )
        await database.value.acceptance_criteria.delete_many({"project_id": project_id, "_id": {"$in": [item["_id"] for item in output_criteria]}})
        await database.value.requirement_versions.delete_many({"project_id": project_id, "transformation_id": transformation["_id"]})
        await database.value.requirements.delete_many({"project_id": project_id, "transformation_id": transformation["_id"]})
        await database.value.requirement_transformations.update_one(
            {"_id": transformation["_id"], "project_id": project_id},
            {"$set": {"status": "FAILED", "error_code": getattr(error, "detail", {"code": type(error).__name__}), "updated_at": now()}},
        )
        raise
    indexed = [await index_requirement(version) for version in output_versions]
    await audit(
        user.id,
        f"requirement_{relation}_confirmed",
        "RequirementTransformation",
        transformation["_id"],
        project_id,
        {
            "source_requirement_ids": transformation["source_requirement_ids"],
            "result_requirement_ids": transformation["result_requirement_ids"],
            "reason": transformation["reason"],
        },
    )
    result = await hydrate_requirement_transformation(transformation)
    return envelope(
        result,
        status="SUCCESS" if all(indexed) else "DEGRADED",
        degraded_mode=None if all(indexed) else "DEGRADED_VECTOR",
    )


@router.post("/du-an/{project_id}/yeu-cau", status_code=201)
async def create_requirement(
    project_id: str,
    payload: RequirementCreate,
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(await create_requirement_record(project_id, payload, user))


@router.get("/du-an/{project_id}/yeu-cau")
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


@router.get("/yeu-cau/{requirement_id}")
async def requirement_detail(requirement_id: str, user: CurrentUser = Depends(get_current_user)):
    requirement = await get_project_entity(
        "requirements", requirement_id, user, "requirement.read"
    )
    version = await database.value.requirement_versions.find_one({"_id": requirement["current_version_id"]})
    criteria = await database.value.acceptance_criteria.find({"requirement_version_id": version["_id"]}).to_list(500)
    return envelope({**requirement, "current_version": {**version, "acceptance_criteria": criteria}})


@router.patch("/du-an/{project_id}/yeu-cau/{requirement_id}")
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
    if "acceptance_criteria" in changes:
        await get_project(project_id, user, "acceptance_criteria.manage")
    if "business_rules" in changes:
        await get_project(project_id, user, "business_rule.manage")
    if "dependencies" in changes:
        await get_project(project_id, user, "requirement_dependency.manage")
    if "attachments" in changes:
        await get_project(project_id, user, "attachment.manage")
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


@router.post("/yeu-cau/{requirement_id}/phu-thuoc")
async def add_requirement_dependency(
    requirement_id: str,
    payload: RequirementDependencyInput,
    user: CurrentUser = Depends(get_current_user),
):
    requirement = await get_project_entity("requirements", requirement_id, user, "requirement_dependency.manage")
    dependency_id = payload.dependency_requirement_id
    if dependency_id == requirement_id:
        raise HTTPException(status_code=422, detail={"code": "REQUIREMENT_DEPENDENCY_CYCLE"})
    dependency = await database.value.requirements.find_one({"_id": dependency_id, "project_id": requirement["project_id"]})
    if not dependency:
        raise HTTPException(status_code=422, detail={"code": "INVALID_REQUIREMENT_DEPENDENCY"})
    version = await database.value.requirement_versions.find_one({"_id": requirement["current_version_id"], "project_id": requirement["project_id"]})
    if not version or version.get("status") != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "IMMUTABLE_REQUIREMENT_VERSION"})
    if version.get("revision") != payload.expected_revision:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT", "current_revision": version.get("revision")})
    dependencies = list(dict.fromkeys(version.get("dependencies", [])))
    if dependency_id in dependencies:
        return envelope(version, revision=version["revision"])
    if await requirement_dependency_reaches(dependency_id, requirement_id, requirement["project_id"]):
        raise HTTPException(status_code=422, detail={"code": "REQUIREMENT_DEPENDENCY_CYCLE"})
    dependencies.append(dependency_id)
    updated = await database.value.requirement_versions.find_one_and_update(
        {"_id": version["_id"], "project_id": requirement["project_id"], "status": "DRAFT", "revision": payload.expected_revision},
        {"$set": {"dependencies": dependencies, "updated_at": now()}, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "requirement_dependency_added", "Requirement", requirement_id, requirement["project_id"], {"dependency_requirement_id": dependency_id})
    return envelope(updated, revision=updated["revision"])


@router.delete("/yeu-cau/{requirement_id}/phu-thuoc/{dependency_requirement_id}")
async def remove_requirement_dependency(
    requirement_id: str,
    dependency_requirement_id: str,
    expected_revision: int = Query(ge=1),
    user: CurrentUser = Depends(get_current_user),
):
    requirement = await get_project_entity("requirements", requirement_id, user, "requirement_dependency.manage")
    version = await database.value.requirement_versions.find_one({"_id": requirement["current_version_id"], "project_id": requirement["project_id"]})
    if not version or version.get("status") != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "IMMUTABLE_REQUIREMENT_VERSION"})
    dependencies = list(dict.fromkeys(version.get("dependencies", [])))
    if dependency_requirement_id not in dependencies:
        return envelope(version, revision=version["revision"])
    updated = await database.value.requirement_versions.find_one_and_update(
        {"_id": version["_id"], "project_id": requirement["project_id"], "status": "DRAFT", "revision": expected_revision},
        {"$set": {"dependencies": [item for item in dependencies if item != dependency_requirement_id], "updated_at": now()}, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "requirement_dependency_removed", "Requirement", requirement_id, requirement["project_id"], {"dependency_requirement_id": dependency_requirement_id})
    return envelope(updated, revision=updated["revision"])


async def requirement_dependency_reaches(start_id: str, target_id: str, project_id: str):
    pending = [start_id]
    visited = set()
    while pending:
        current_id = pending.pop()
        if current_id == target_id:
            return True
        if current_id in visited:
            continue
        visited.add(current_id)
        requirement = await database.value.requirements.find_one({"_id": current_id, "project_id": project_id}, {"current_version_id": 1})
        if not requirement:
            continue
        version = await database.value.requirement_versions.find_one({"_id": requirement.get("current_version_id"), "project_id": project_id}, {"dependencies": 1})
        pending.extend((version or {}).get("dependencies", []))
    return False


@router.post("/yeu-cau/{requirement_id}/phien-ban", status_code=201)
async def create_requirement_version(
    requirement_id: str,
    payload: RequirementVersionCreate,
    user: CurrentUser = Depends(get_current_user),
):
    requirement = await get_project_entity(
        "requirements", requirement_id, user, "requirement.version.create"
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


@router.get("/yeu-cau/{requirement_id}/phien-ban")
async def list_requirement_versions(requirement_id: str, user: CurrentUser = Depends(get_current_user)):
    requirement = await get_project_entity(
        "requirements", requirement_id, user, "requirement.version.read"
    )
    versions = await database.value.requirement_versions.find({"requirement_id": requirement_id}).sort("version", -1).to_list(500)
    return envelope(versions)


@router.post("/du-an/{project_id}/yeu-cau/{requirement_id}/gui-ra-soat")
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
    project = await database.value.projects.find_one({"_id": project_id}, {"settings": 1})
    lint_blocking = (project.get("settings") or {}).get("requirement_lint_blocking", True)
    if lint_blocking and any(item["severity"] == "error" for item in findings):
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


@router.post("/yeu-cau/{requirement_id}/ra-soat")
async def submit_requirement_review_alias(
    requirement_id: str,
    payload: ReviewTransitionInput,
    user: CurrentUser = Depends(get_current_user),
):
    requirement = await get_project_entity("requirements", requirement_id, user, "requirement.submit_review")
    return await submit_requirement_review(requirement["project_id"], requirement_id, payload, user)


@router.post("/du-an/{project_id}/yeu-cau/{requirement_id}/yeu-cau-chinh-sua")
async def request_requirement_changes(
    project_id: str,
    requirement_id: str,
    payload: ReviewTransitionInput,
    user: CurrentUser = Depends(get_current_user),
):
    requirement = await get_project_entity(
        "requirements", requirement_id, user, "requirement.review"
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


@router.post("/phien-ban-yeu-cau/{version_id}/chot-chuan")
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
    project = await database.value.projects.find_one(
        {"_id": version["project_id"]}, {"settings": 1}
    )
    lint_blocking = (project.get("settings") or {}).get("requirement_lint_blocking", True)
    if lint_blocking and any(item["severity"] == "error" for item in findings):
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


@router.post("/du-an/{project_id}/yeu-cau/{requirement_id}/phe-duyet")
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


@router.post("/yeu-cau/{requirement_id}/phe-duyet")
async def approve_requirement_alias(
    requirement_id: str,
    payload: RequirementBaselineInput,
    user: CurrentUser = Depends(get_current_user),
):
    requirement = await get_project_entity("requirements", requirement_id, user, "requirement.approve")
    return await baseline_requirement_version(requirement["current_version_id"], payload, user)


@router.post("/yeu-cau/{requirement_id}/ngung-hieu-luc")
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
    current_version = await database.value.requirement_versions.find_one(
        {
            "_id": payload.expected_current_version_id,
            "project_id": requirement["project_id"],
            "requirement_id": requirement_id,
        }
    )
    if not current_version or current_version.get("status") not in {
        "DRAFT",
        "IN_REVIEW",
        "BASELINED",
    }:
        raise HTTPException(status_code=409, detail={"code": "REQUIREMENT_VERSION_CONFLICT"})
    version_status = current_version["status"]
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
                "status_before_obsolete": requirement["status"],
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
                "status_before_obsolete": version_status,
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
                    "status_before_obsolete": "",
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


@router.post("/yeu-cau/{requirement_id}/khoi-phuc")
async def restore_requirement(
    requirement_id: str,
    payload: RequirementRestoreInput,
    user: CurrentUser = Depends(get_current_user),
):
    requirement = await get_project_entity(
        "requirements", requirement_id, user, "requirement.restore"
    )
    if requirement.get("status") != "OBSOLETE":
        raise HTTPException(status_code=409, detail={"code": "REQUIREMENT_NOT_OBSOLETE"})
    if requirement.get("current_version_id") != payload.expected_current_version_id:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "REVISION_CONFLICT",
                "current_version_id": requirement.get("current_version_id"),
            },
        )
    version = await database.value.requirement_versions.find_one(
        {
            "_id": payload.expected_current_version_id,
            "project_id": requirement["project_id"],
            "requirement_id": requirement_id,
            "status": "OBSOLETE",
        }
    )
    if not version:
        raise HTTPException(status_code=409, detail={"code": "REQUIREMENT_VERSION_CONFLICT"})
    restored_status = requirement.get("status_before_obsolete") or (
        "BASELINED" if version.get("baselined_at") else "DRAFT"
    )
    restored_version_status = version.get("status_before_obsolete") or restored_status
    if restored_status not in {"DRAFT", "IN_REVIEW", "BASELINED"} or restored_version_status not in {
        "DRAFT",
        "IN_REVIEW",
        "BASELINED",
    }:
        raise HTTPException(status_code=409, detail={"code": "REQUIREMENT_RESTORE_STATE_INVALID"})
    timestamp = now()
    version_result = await database.value.requirement_versions.update_one(
        {
            "_id": version["_id"],
            "project_id": requirement["project_id"],
            "requirement_id": requirement_id,
            "status": "OBSOLETE",
        },
        {
            "$set": {
                "status": restored_version_status,
                "restore_reason": payload.reason,
                "restored_by": user.id,
                "restored_at": timestamp,
                "updated_at": timestamp,
            },
            "$unset": {
                "status_before_obsolete": "",
                "obsolete_reason": "",
                "obsolete_by": "",
                "obsolete_at": "",
            },
            "$inc": {"revision": 1},
        },
    )
    if version_result.matched_count != 1:
        raise HTTPException(status_code=409, detail={"code": "REQUIREMENT_VERSION_CONFLICT"})
    updated = await database.value.requirements.find_one_and_update(
        {
            "_id": requirement_id,
            "project_id": requirement["project_id"],
            "current_version_id": payload.expected_current_version_id,
            "status": "OBSOLETE",
        },
        {
            "$set": {
                "status": restored_status,
                "restore_reason": payload.reason,
                "restored_by": user.id,
                "restored_at": timestamp,
                "updated_at": timestamp,
            },
            "$unset": {
                "status_before_obsolete": "",
                "obsolete_reason": "",
                "obsolete_by": "",
                "obsolete_at": "",
            },
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        await database.value.requirement_versions.update_one(
            {"_id": version["_id"], "project_id": requirement["project_id"]},
            {
                "$set": {
                    "status": "OBSOLETE",
                    "status_before_obsolete": restored_version_status,
                    "updated_at": now(),
                },
                "$inc": {"revision": 1},
            },
        )
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "requirement_restored",
        "Requirement",
        requirement_id,
        requirement["project_id"],
        {"reason": payload.reason, "version_id": version["_id"]},
    )
    restored_version = await database.value.requirement_versions.find_one(
        {"_id": version["_id"], "project_id": requirement["project_id"]}
    )
    return envelope({**updated, "current_version": restored_version})


@router.post("/phien-ban-yeu-cau/{version_id}/ai/kiem-tra")
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


@router.post("/du-an/{project_id}/yeu-cau/{requirement_id}/kiem-tra")
async def lint_requirement_draft(project_id: str, requirement_id: str, user: CurrentUser = Depends(get_current_user)):
    requirement = await get_project_entity("requirements", requirement_id, user, "ai.run_lint")
    if requirement["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    return await lint_requirement(requirement["current_version_id"], user)


@router.post("/yeu-cau/{requirement_id}/kiem-tra")
async def lint_requirement_alias(requirement_id: str, user: CurrentUser = Depends(get_current_user)):
    requirement = await get_project_entity("requirements", requirement_id, user, "ai.run_lint")
    return await lint_requirement(requirement["current_version_id"], user)


@router.post("/yeu-cau/{requirement_id}/so-sanh")
async def compare_requirement(
    requirement_id: str,
    payload: RequirementCompareInput,
    user: CurrentUser = Depends(get_current_user),
):
    requirement = await get_project_entity(
        "requirements", requirement_id, user, "requirement.diff.read"
    )
    versions = await database.value.requirement_versions.find(
        {"requirement_id": requirement_id, "_id": {"$in": [payload.from_version_id, payload.to_version_id]}}
    ).to_list(2)
    by_id = {item["_id"]: item for item in versions}
    if set(by_id) != {payload.from_version_id, payload.to_version_id}:
        raise HTTPException(status_code=404, detail="Không tìm thấy đủ hai phiên bản")
    changes = semantic_changes(by_id[payload.from_version_id], by_id[payload.to_version_id])
    return envelope({"from_version": by_id[payload.from_version_id], "to_version": by_id[payload.to_version_id], "changes": changes, "comparison_algorithm_version": "semantic-diff-v1"})


@router.get("/yeu-cau/{requirement_id}/khac-biet")
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


@router.post("/du-an/{project_id}/yeu-cau/{requirement_id}/tach", status_code=201)
async def split_requirement(
    project_id: str,
    requirement_id: str,
    payload: RequirementSplitInput,
    user: CurrentUser = Depends(get_current_user),
):
    expected_versions = {requirement_id: payload.expected_source_version_id}
    await get_project(project_id, user, "requirement.split")
    existing = await database.value.requirement_transformations.find_one(
        {"project_id": project_id, "idempotency_key": payload.idempotency_key}
    )
    sources = None
    if not existing:
        sources = await load_requirement_baselines(
            project_id,
            [requirement_id],
            expected_versions,
            user,
            "requirement.split",
        )
    transformation, execute = await claim_requirement_transformation(
        project_id,
        "SPLIT",
        payload,
        [requirement_id],
        [payload.expected_source_version_id],
        user,
    )
    if not execute:
        return envelope(await hydrate_requirement_transformation(transformation))
    if sources is None:
        sources = await load_requirement_baselines(
            project_id,
            [requirement_id],
            expected_versions,
            user,
            "requirement.split",
        )
    return await execute_requirement_transformation(
        project_id,
        transformation,
        sources,
        payload.drafts,
        user,
        "split",
    )


@router.post("/du-an/{project_id}/yeu-cau/gop", status_code=201)
async def merge_requirements(
    project_id: str,
    payload: RequirementMergeInput,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "requirement.merge")
    existing = await database.value.requirement_transformations.find_one(
        {"project_id": project_id, "idempotency_key": payload.idempotency_key}
    )
    sources = None
    if not existing:
        sources = await load_requirement_baselines(
            project_id,
            payload.source_requirement_ids,
            payload.expected_source_version_ids,
            user,
            "requirement.merge",
        )
    transformation, execute = await claim_requirement_transformation(
        project_id,
        "MERGE",
        payload,
        payload.source_requirement_ids,
        [payload.expected_source_version_ids[item] for item in payload.source_requirement_ids],
        user,
    )
    if not execute:
        return envelope(await hydrate_requirement_transformation(transformation))
    if sources is None:
        sources = await load_requirement_baselines(
            project_id,
            payload.source_requirement_ids,
            payload.expected_source_version_ids,
            user,
            "requirement.merge",
        )
    return await execute_requirement_transformation(
        project_id,
        transformation,
        sources,
        [payload.draft],
        user,
        "merge",
    )


@router.post("/du-an/{project_id}/yeu-cau/kiem-tra-trung-lap", status_code=201)
async def find_duplicate_requirements(
    project_id: str,
    payload: RequirementDuplicateCheckInput,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "requirement.duplicate_check")
    query = {"project_id": project_id, "status": {"$nin": ["OBSOLETE", "ARCHIVED"]}}
    selected_ids = list(dict.fromkeys(payload.requirement_ids))
    if selected_ids:
        query["_id"] = {"$in": selected_ids}
    requirements = await database.value.requirements.find(query).to_list(500)
    if selected_ids and {item["_id"] for item in requirements} != set(selected_ids):
        raise HTTPException(status_code=404, detail={"code": "REQUIREMENT_SELECTION_NOT_FOUND"})
    versions = await database.value.requirement_versions.find(
        {
            "project_id": project_id,
            "_id": {"$in": [item["current_version_id"] for item in requirements]},
        }
    ).to_list(500)
    criteria = await database.value.acceptance_criteria.find(
        {"project_id": project_id, "requirement_version_id": {"$in": [item["_id"] for item in versions]}}
    ).to_list(10000)
    criteria_by_version = {}
    for criterion in criteria:
        criteria_by_version.setdefault(criterion["requirement_version_id"], []).append(criterion)
    version_by_id = {item["_id"]: {**item, "acceptance_criteria": criteria_by_version.get(item["_id"], [])} for item in versions}
    candidates = []
    ordered = sorted(requirements, key=lambda item: item["_id"])
    for index, left in enumerate(ordered):
        left_version = version_by_id.get(left["current_version_id"])
        if not left_version:
            continue
        for right in ordered[index + 1 :]:
            right_version = version_by_id.get(right["current_version_id"])
            if not right_version:
                continue
            score, reasons = requirement_duplicate_score(left_version, right_version)
            if score < payload.threshold:
                continue
            candidates.append(
                {
                    "left_requirement_id": left["_id"],
                    "left_version_id": left_version["_id"],
                    "right_requirement_id": right["_id"],
                    "right_version_id": right_version["_id"],
                    "score": score,
                    "match_type": "EXACT" if score == 1 else "SEMANTIC",
                    "reasons": reasons,
                    "status": "CANDIDATE",
                }
            )
    candidates.sort(key=lambda item: (-item["score"], item["left_requirement_id"], item["right_requirement_id"]))
    candidates = candidates[: payload.limit]
    scan = {
        "_id": new_id("RDS"),
        "project_id": project_id,
        "requirement_ids": selected_ids,
        "threshold": payload.threshold,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "algorithm": {
            "name": "requirement-duplicate-v1",
            "lexical_weight": 0.65,
            "term_weight": 0.25,
            "business_rule_weight": 0.1,
        },
        "status": "COMPLETED",
        "created_by": user.id,
        "created_at": now(),
    }
    await database.value.requirement_duplicate_scans.insert_one(scan)
    await audit(
        user.id,
        "requirement_duplicate_scan_completed",
        "RequirementDuplicateScan",
        scan["_id"],
        project_id,
        {"candidate_count": len(candidates), "threshold": payload.threshold},
    )
    return envelope(scan)


@router.post("/du-an/{project_id}/tai-lieu-yeu-cau", status_code=201)
async def create_requirement_document(
    project_id: str,
    payload: ImportCreate,
    user: CurrentUser = Depends(get_current_user),
):
    document = await create_requirement_document_record(project_id, payload, user)
    return envelope(document, revision=document["revision"])


@router.post("/du-an/{project_id}/tai-lieu-yeu-cau/tai-len", status_code=201)
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
    await get_project(project_id, user, "requirement_document.upload")
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
        "source_version": 1,
        "source_type": "reference",
        "authority": "reference",
        "status": "UPLOADED",
        "index_status": "PENDING",
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
    indexed = await index_artifact(project_id, "requirement_document", document_id, document_id, filename, normalized, document["status"], document["authority"], document["source_version"])
    await database.value.requirement_documents.update_one({"_id": document_id, "project_id": project_id}, {"$set": {"index_status": "INDEXED" if indexed else "FAILED", "indexed_at": now()}})
    document = await database.value.requirement_documents.find_one({"_id": document_id, "project_id": project_id})
    return envelope(document, revision=document["revision"], status="SUCCESS" if indexed else "DEGRADED", degraded_mode=None if indexed else "DEGRADED_VECTOR")


@router.get("/du-an/{project_id}/tai-lieu-yeu-cau")
async def list_requirement_documents(
    project_id: str,
    status: str = Query(default="", max_length=30),
    q: str = Query(default="", max_length=200),
    limit: int = Query(default=200, ge=1, le=1000),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "requirement_document.read")
    query = {"project_id": project_id}
    if status:
        query["status"] = status.upper()
    if q:
        query["filename"] = {"$regex": re.escape(q), "$options": "i"}
    documents = (
        await database.value.requirement_documents.find(query)
        .sort("updated_at", -1)
        .limit(limit)
        .to_list(limit)
    )
    return envelope(documents)


@router.post("/du-an/{project_id}/nguon-tri-thuc", status_code=201)
async def create_knowledge_source(
    project_id: str,
    payload: KnowledgeSourceCreate,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "knowledge.manage")
    content_hash = hashlib.sha256(payload.content.encode("utf-8")).hexdigest()
    existing = await database.value.requirement_documents.find_one(
        {"project_id": project_id, "content_hash": content_hash}
    )
    if existing:
        return envelope(existing, revision=existing.get("revision", 1))
    timestamp = now()
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "-", payload.title).strip("-") or "knowledge-source"
    document = {
        "_id": new_id("KSRC"),
        "project_id": project_id,
        "filename": f"{safe_name}.md",
        "format": "md",
        "content_hash": content_hash,
        "raw_source": {
            "storage": "embedded",
            "content": payload.content,
            "sha256": content_hash,
            "size": len(payload.content.encode("utf-8")),
            "source_url": payload.source_url,
        },
        "normalized_content": payload.content,
        "normalized_content_hash": content_hash,
        "source_version": 1,
        "title": payload.title,
        "source_type": payload.source_type,
        "authority": payload.authority,
        "source_url": payload.source_url,
        "teacher_id": payload.teacher_id,
        "subject": payload.subject,
        "grade": payload.grade,
        "tags": payload.tags,
        "status": "READY",
        "index_status": "PENDING",
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    await database.value.requirement_documents.insert_one(document)
    indexed = await index_artifact(
        project_id,
        "requirement_document",
        document["_id"],
        document["_id"],
        payload.title,
        payload.content,
        document["status"],
        payload.authority,
        1,
    )
    document["index_status"] = "INDEXED" if indexed else "FAILED"
    document["indexed_at"] = now()
    await database.value.requirement_documents.update_one(
        {"_id": document["_id"], "project_id": project_id},
        {"$set": {"index_status": document["index_status"], "indexed_at": document["indexed_at"]}},
    )
    await audit(
        user.id,
        "knowledge_source_created",
        "RequirementDocument",
        document["_id"],
        project_id,
        {"source_type": payload.source_type, "authority": payload.authority},
    )
    return envelope(
        document,
        revision=1,
        status="SUCCESS" if indexed else "DEGRADED",
        degraded_mode=None if indexed else "DEGRADED_VECTOR",
    )


@router.get("/du-an/{project_id}/nguon-tri-thuc")
async def list_knowledge_sources(
    project_id: str,
    include_archived: bool = Query(default=False),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "knowledge.read")
    query = {"project_id": project_id}
    if not include_archived:
        query["status"] = {"$ne": "ARCHIVED"}
    documents = await database.value.requirement_documents.find(query).sort("updated_at", -1).to_list(1000)
    order = (await database.value.projects.find_one({"_id": project_id}, {"settings.knowledge_authority_order": 1}) or {}).get("settings", {}).get(
        "knowledge_authority_order",
        ["teacher", "official", "baseline", "supplemental", "reference"],
    )
    ranks = {value: index for index, value in enumerate(order)}
    documents.sort(key=lambda item: (ranks.get(item.get("authority"), len(ranks)), item.get("updated_at")))
    return envelope(documents)


@router.post("/nguon-tri-thuc/{document_id}/luu-tru")
async def archive_knowledge_source(
    document_id: str,
    payload: ProjectArchiveInput,
    user: CurrentUser = Depends(get_current_user),
):
    document = await get_project_entity(
        "requirement_documents", document_id, user, "knowledge.manage"
    )
    await require_action_policy(
        document["project_id"], user, "knowledge.archive", {"QA_LEAD", "BA"}
    )
    if document.get("status") == "ARCHIVED":
        return envelope(document, revision=document["revision"])
    updated = await database.value.requirement_documents.find_one_and_update(
        {
            "_id": document_id,
            "project_id": document["project_id"],
            "revision": payload.expected_revision,
        },
        {
            "$set": {
                "status_before_archive": document.get("status", "READY"),
                "status": "ARCHIVED",
                "archived_by": user.id,
                "archived_at": now(),
                "archive_reason": payload.reason,
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
        "knowledge_source_archived",
        "RequirementDocument",
        document_id,
        document["project_id"],
        {"reason": payload.reason},
    )
    return envelope(updated, revision=updated["revision"])


@router.get("/tai-lieu-yeu-cau/{document_id}")
async def get_requirement_document(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    document = await get_project_entity(
        "requirement_documents", document_id, user, "requirement_document.read"
    )
    return envelope(document, revision=document["revision"])


@router.patch("/tai-lieu-yeu-cau/{document_id}")
async def update_requirement_document_metadata(
    document_id: str,
    payload: RequirementDocumentPatch,
    user: CurrentUser = Depends(get_current_user),
):
    document = await get_project_entity("requirement_documents", document_id, user, "knowledge.manage")
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    updated = await database.value.requirement_documents.find_one_and_update(
        {"_id": document_id, "project_id": document["project_id"], "revision": payload.expected_revision},
        {"$set": {**changes, "updated_at": now()}, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "requirement_document_metadata_updated", "RequirementDocument", document_id, document["project_id"], {"fields": sorted(changes)})
    return envelope(updated, revision=updated["revision"])


@router.post("/tai-lieu-yeu-cau/{document_id}/lap-chi-muc-lai", status_code=202)
async def reindex_requirement_document(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    document = await get_project_entity("requirement_documents", document_id, user, "knowledge.manage")
    if document.get("status") == "ARCHIVED":
        raise HTTPException(status_code=409, detail={"code": "DOCUMENT_ARCHIVED"})
    normalized = serialized_content(document.get("normalized_content") or "")
    indexed = await index_artifact(
        document["project_id"],
        "requirement_document",
        document_id,
        document_id,
        document.get("title") or document.get("filename") or document_id,
        normalized,
        document.get("status", "READY"),
        document.get("authority", "reference"),
        document.get("source_version", 1),
    )
    await database.value.requirement_documents.update_one(
        {"_id": document_id, "project_id": document["project_id"]},
        {"$set": {"index_status": "INDEXED" if indexed else "FAILED", "indexed_at": now(), "updated_at": now()}, "$inc": {"revision": 1}},
    )
    updated = await database.value.requirement_documents.find_one({"_id": document_id, "project_id": document["project_id"]})
    await audit(user.id, "requirement_document_reindexed", "RequirementDocument", document_id, document["project_id"], {"indexed": indexed})
    return envelope(updated, revision=updated["revision"], status="SUCCESS" if indexed else "DEGRADED", degraded_mode=None if indexed else "DEGRADED_VECTOR")


@router.get("/tai-lieu-yeu-cau/{document_id}/tai-xuong")
async def download_requirement_document(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    document = await get_project_entity(
        "requirement_documents",
        document_id,
        user,
        "requirement_document.download",
    )
    data = await read_raw_requirement_source(document)
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", document.get("filename") or "source.bin")
    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/tai-lieu-yeu-cau/{document_id}/luu-tru")
async def archive_requirement_document(
    document_id: str,
    payload: ProjectArchiveInput,
    user: CurrentUser = Depends(get_current_user),
):
    document = await get_project_entity(
        "requirement_documents",
        document_id,
        user,
        "requirement_document.archive",
    )
    if document.get("status") == "ARCHIVED":
        return envelope(document, revision=document["revision"])
    updated = await database.value.requirement_documents.find_one_and_update(
        {
            "_id": document_id,
            "project_id": document["project_id"],
            "revision": payload.expected_revision,
        },
        {
            "$set": {
                "status_before_archive": document.get("status", "READY"),
                "status": "ARCHIVED",
                "archived_by": user.id,
                "archived_at": now(),
                "archive_reason": payload.reason,
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
        "requirement_document_archived",
        "RequirementDocument",
        document_id,
        document["project_id"],
        {"reason": payload.reason},
    )
    return envelope(updated, revision=updated["revision"])


@router.post("/tai-lieu-yeu-cau/{document_id}/khoi-phuc")
async def restore_requirement_document(
    document_id: str,
    payload: ProjectArchiveInput,
    user: CurrentUser = Depends(get_current_user),
):
    document = await get_project_entity(
        "requirement_documents",
        document_id,
        user,
        "requirement_document.restore",
    )
    if document.get("status") != "ARCHIVED":
        return envelope(document, revision=document["revision"])
    updated = await database.value.requirement_documents.find_one_and_update(
        {
            "_id": document_id,
            "project_id": document["project_id"],
            "revision": payload.expected_revision,
            "status": "ARCHIVED",
        },
        {
            "$set": {
                "status": document.get("status_before_archive", "READY"),
                "restored_by": user.id,
                "restored_at": now(),
                "restore_reason": payload.reason,
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
        "requirement_document_restored",
        "RequirementDocument",
        document_id,
        document["project_id"],
        {"reason": payload.reason},
    )
    return envelope(updated, revision=updated["revision"])


@router.post("/tai-lieu-yeu-cau/{document_id}/thu-lai-phan-tich")
async def retry_requirement_document_parse(
    document_id: str,
    payload: RequirementParseRetry,
    user: CurrentUser = Depends(get_current_user),
):
    document = await get_project_entity(
        "requirement_documents", document_id, user, "requirement_document.extract"
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


@router.post("/tai-lieu-yeu-cau/{document_id}/trich-xuat", status_code=201)
async def extract_requirement_document(
    document_id: str,
    payload: RequirementExtractionInput,
    user: CurrentUser = Depends(get_current_user),
):
    document = await get_project_entity(
        "requirement_documents", document_id, user, "requirement_document.extract"
    )
    if document.get("status") == "ARCHIVED":
        raise HTTPException(status_code=409, detail={"code": "DOCUMENT_ARCHIVED"})
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
    job_id = new_id("RIMP")
    candidates = prepare_requirement_candidates(job_id, atomic_requirement_candidates(document))
    job = {
        "_id": job_id,
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


@router.post("/du-an/{project_id}/nhap-yeu-cau", status_code=201)
async def create_requirement_import(
    project_id: str,
    payload: ImportCreate,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "requirement.create")
    job_id = new_id("RIMP")
    previews = prepare_requirement_candidates(job_id, parse_import(payload))
    job = {
        "_id": job_id,
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


@router.post("/du-an/{project_id}/nhap-yeu-cau/tai-len", status_code=201)
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


@router.get("/nhap-yeu-cau/{job_id}")
async def get_requirement_import(job_id: str, user: CurrentUser = Depends(get_current_user)):
    job = await get_project_entity("import_jobs", job_id, user, "requirement_document.review_extraction")
    return envelope(job, revision=job.get("revision", 1))


@router.patch("/nhap-yeu-cau/{job_id}")
async def review_requirement_import(
    job_id: str,
    payload: RequirementImportReview,
    user: CurrentUser = Depends(get_current_user),
):
    job = await get_project_entity("import_jobs", job_id, user, "requirement_document.review_extraction")
    if job.get("status") != "PREVIEW_READY":
        raise HTTPException(
            status_code=409,
            detail={"code": "IMPORT_PREVIEW_NOT_EDITABLE", "status": job.get("status")},
        )
    current_preview = prepare_requirement_candidates(job_id, job.get("preview", []))
    submitted = [candidate.model_dump() for candidate in payload.preview]
    if len(submitted) == len(current_preview) and all(not item.get("candidate_id") for item in submitted):
        for index, item in enumerate(submitted):
            item["candidate_id"] = current_preview[index]["candidate_id"]
    current_by_id = {item["candidate_id"]: item for item in current_preview}
    submitted_by_id = {item.get("candidate_id"): item for item in submitted}
    if None in submitted_by_id or set(submitted_by_id) != set(current_by_id):
        raise HTTPException(status_code=422, detail={"code": "CANDIDATE_SET_CHANGED"})
    preview = []
    for current in current_preview:
        candidate = submitted_by_id[current["candidate_id"]]
        candidate["source_refs"] = current.get("source_refs", [])
        candidate["candidate_status"] = "ACTIVE"
        candidate["candidate_revision"] = int(current.get("candidate_revision", 1)) + 1
        candidate["candidate_relation"] = current.get("candidate_relation")
        candidate["parent_candidate_ids"] = current.get("parent_candidate_ids", [])
        preview.append(candidate)
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


@router.post("/nhap-yeu-cau/{job_id}/ung-vien/gop")
async def merge_requirement_candidates(
    job_id: str,
    payload: RequirementCandidateMergeInput,
    user: CurrentUser = Depends(get_current_user),
):
    job = await get_project_entity("import_jobs", job_id, user, "requirement_document.review_extraction")
    if job.get("status") != "PREVIEW_READY":
        raise HTTPException(status_code=409, detail={"code": "IMPORT_PREVIEW_NOT_EDITABLE"})
    candidate_ids = list(dict.fromkeys(payload.candidate_ids))
    if len(candidate_ids) != len(payload.candidate_ids):
        raise HTTPException(status_code=422, detail={"code": "DUPLICATE_CANDIDATE_ID"})
    preview = prepare_requirement_candidates(job_id, job.get("preview", []))
    by_id = {item["candidate_id"]: item for item in preview}
    if not set(candidate_ids) <= set(by_id):
        raise HTTPException(status_code=404, detail={"code": "CANDIDATE_NOT_FOUND"})
    parents = [by_id[item] for item in candidate_ids]
    merged = payload.merged.model_dump()
    validate_doc(merged["content_doc"])
    for criterion in merged.get("acceptance_criteria", []):
        validate_doc(criterion["content_doc"])
    merged["source_refs"] = unique_source_refs(
        [source for parent in parents for source in parent.get("source_refs", [])]
        + merged.get("source_refs", [])
    )
    await validate_requirement_sources(job["project_id"], merged["source_refs"])
    merged_id = new_id("RCAND")
    merged.update(
        {
            "candidate_id": merged_id,
            "candidate_status": "ACTIVE",
            "candidate_revision": 1,
            "candidate_relation": "merged",
            "parent_candidate_ids": candidate_ids,
            "extraction_confidence": min(
                (float(item.get("extraction_confidence", 1)) for item in parents),
                default=1,
            ),
        }
    )
    first_index = min(index for index, item in enumerate(preview) if item["candidate_id"] in candidate_ids)
    next_preview = [item for item in preview if item["candidate_id"] not in candidate_ids]
    next_preview.insert(first_index, merged)
    event = {
        "_id": new_id("RCOP"),
        "type": "MERGE",
        "parent_candidate_ids": candidate_ids,
        "result_candidate_ids": [merged_id],
        "parent_fingerprints": [candidate_fingerprint(item) for item in parents],
        "source_refs": merged["source_refs"],
        "reason": payload.reason,
        "actor_id": user.id,
        "created_at": now(),
    }
    updated = await database.value.import_jobs.find_one_and_update(
        {
            "_id": job_id,
            "project_id": job["project_id"],
            "status": "PREVIEW_READY",
            "revision": payload.expected_revision,
        },
        {
            "$set": {
                "preview": next_preview,
                "candidate_count": len(next_preview),
                "reviewed_by": user.id,
                "reviewed_at": now(),
                "updated_at": now(),
            },
            "$push": {"candidate_lineage": event},
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "requirement_candidates_merged",
        "RequirementImport",
        job_id,
        job["project_id"],
        {"parent_candidate_ids": candidate_ids, "result_candidate_id": merged_id, "reason": payload.reason},
    )
    return envelope(updated, revision=updated["revision"])


@router.post("/nhap-yeu-cau/{job_id}/ung-vien/{candidate_id}/tach")
async def split_requirement_candidate(
    job_id: str,
    candidate_id: str,
    payload: RequirementCandidateSplitInput,
    user: CurrentUser = Depends(get_current_user),
):
    job = await get_project_entity("import_jobs", job_id, user, "requirement_document.review_extraction")
    if job.get("status") != "PREVIEW_READY":
        raise HTTPException(status_code=409, detail={"code": "IMPORT_PREVIEW_NOT_EDITABLE"})
    preview = prepare_requirement_candidates(job_id, job.get("preview", []))
    parent = next((item for item in preview if item["candidate_id"] == candidate_id), None)
    if not parent:
        raise HTTPException(status_code=404, detail={"code": "CANDIDATE_NOT_FOUND"})
    if len(preview) - 1 + len(payload.drafts) > 500:
        raise HTTPException(status_code=422, detail={"code": "CANDIDATE_LIMIT_EXCEEDED"})
    children = []
    for index, draft in enumerate(payload.drafts):
        child = draft.model_dump()
        validate_doc(child["content_doc"])
        for criterion in child.get("acceptance_criteria", []):
            validate_doc(criterion["content_doc"])
        child["source_refs"] = unique_source_refs(
            parent.get("source_refs", []) + child.get("source_refs", [])
        )
        await validate_requirement_sources(job["project_id"], child["source_refs"])
        child.update(
            {
                "candidate_id": new_id("RCAND"),
                "candidate_status": "ACTIVE",
                "candidate_revision": 1,
                "candidate_relation": f"split-{index + 1}",
                "parent_candidate_ids": [candidate_id],
                "extraction_confidence": float(parent.get("extraction_confidence", 1)),
            }
        )
        children.append(child)
    parent_index = next(index for index, item in enumerate(preview) if item["candidate_id"] == candidate_id)
    next_preview = list(preview)
    next_preview[parent_index : parent_index + 1] = children
    event = {
        "_id": new_id("RCOP"),
        "type": "SPLIT",
        "parent_candidate_ids": [candidate_id],
        "result_candidate_ids": [item["candidate_id"] for item in children],
        "parent_fingerprints": [candidate_fingerprint(parent)],
        "source_refs": parent.get("source_refs", []),
        "reason": payload.reason,
        "actor_id": user.id,
        "created_at": now(),
    }
    updated = await database.value.import_jobs.find_one_and_update(
        {
            "_id": job_id,
            "project_id": job["project_id"],
            "status": "PREVIEW_READY",
            "revision": payload.expected_revision,
        },
        {
            "$set": {
                "preview": next_preview,
                "candidate_count": len(next_preview),
                "reviewed_by": user.id,
                "reviewed_at": now(),
                "updated_at": now(),
            },
            "$push": {"candidate_lineage": event},
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "requirement_candidate_split",
        "RequirementImport",
        job_id,
        job["project_id"],
        {
            "parent_candidate_id": candidate_id,
            "result_candidate_ids": [item["candidate_id"] for item in children],
            "reason": payload.reason,
        },
    )
    return envelope(updated, revision=updated["revision"])


@router.post("/nhap-yeu-cau/{job_id}/ung-vien/{candidate_id}/tu-choi")
async def reject_requirement_candidate(
    job_id: str,
    candidate_id: str,
    payload: RequirementCandidateRejectInput,
    user: CurrentUser = Depends(get_current_user),
):
    job = await get_project_entity("import_jobs", job_id, user, "requirement_document.review_extraction")
    if job.get("status") != "PREVIEW_READY":
        raise HTTPException(status_code=409, detail={"code": "IMPORT_PREVIEW_NOT_EDITABLE"})
    preview = prepare_requirement_candidates(job_id, job.get("preview", []))
    candidate = next((item for item in preview if item["candidate_id"] == candidate_id), None)
    if not candidate:
        rejected = next(
            (
                item
                for item in job.get("rejected_candidates", [])
                if item.get("candidate_id") == candidate_id
            ),
            None,
        )
        if rejected:
            return envelope(job, revision=job["revision"])
        raise HTTPException(status_code=404, detail={"code": "CANDIDATE_NOT_FOUND"})
    rejected = {
        **candidate,
        "candidate_status": "REJECTED",
        "candidate_revision": int(candidate.get("candidate_revision", 1)) + 1,
        "rejection_reason": payload.reason,
        "rejected_by": user.id,
        "rejected_at": now(),
    }
    next_preview = [item for item in preview if item["candidate_id"] != candidate_id]
    updated = await database.value.import_jobs.find_one_and_update(
        {
            "_id": job_id,
            "project_id": job["project_id"],
            "status": "PREVIEW_READY",
            "revision": payload.expected_revision,
        },
        {
            "$set": {
                "preview": next_preview,
                "candidate_count": len(next_preview),
                "reviewed_by": user.id,
                "reviewed_at": now(),
                "updated_at": now(),
            },
            "$push": {"rejected_candidates": rejected},
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "requirement_candidate_rejected",
        "RequirementImport",
        job_id,
        job["project_id"],
        {"candidate_id": candidate_id, "reason": payload.reason},
    )
    return envelope(updated, revision=updated["revision"])


@router.post("/nhap-yeu-cau/{job_id}/xac-nhan")
async def confirm_requirement_import(
    job_id: str,
    payload: ImportConfirm,
    user: CurrentUser = Depends(get_current_user),
):
    job = await get_project_entity(
        "import_jobs", job_id, user, "requirement_document.confirm_extraction"
    )
    await get_project(job["project_id"], user, "requirement.create")
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
