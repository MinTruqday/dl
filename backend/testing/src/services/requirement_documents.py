import hashlib
import re
from dataclasses import dataclass

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.clients.storage import storage_client
from src.core.common import audit, get_project, get_project_entity, new_id, now
from src.core.configuration import settings
from src.repositories import requirement_document_repository
from src.clients.project_knowledge import index_artifact
from src.services.requirement_import import (
    extract_file_content,
    supported_requirement_formats,
)
from src.services.requirement_workflow import serialized_content
from src.services.domain_policy import domain_policy


DOCUMENT_POLICY = domain_policy("requirement_documents")


@dataclass(frozen=True)
class RequirementDocumentResult:
    data: dict
    status: str = DOCUMENT_POLICY["result_statuses"]["success"]
    degraded_mode: str | None = None


async def create_requirement_document_record(project_id, payload, user):
    policy = DOCUMENT_POLICY
    statuses = policy["statuses"]
    index_statuses = policy["index_statuses"]
    codes = policy["error_codes"]
    await get_project(project_id, user, policy["permissions"]["upload"])
    content = serialized_content(payload.content)
    if len(content.encode("utf-8")) > settings.MAX_REQUIREMENT_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail={"code": codes["import_too_large"]})
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    existing = await requirement_document_repository.find_by_hash(project_id, content_hash)
    if existing:
        return existing
    timestamp = now()
    document = {
        "_id": new_id(policy["id_prefix"]),
        "project_id": project_id,
        "filename": payload.filename,
        "format": payload.format,
        "content_hash": content_hash,
        "raw_source": {
            "storage": policy["embedded_storage"],
            "content": payload.content,
            "sha256": content_hash,
            "size": len(content.encode("utf-8")),
        },
        "normalized_content": payload.content,
        "normalized_content_hash": content_hash,
        "source_version": policy["source_version"],
        "source_type": policy["source_type"],
        "authority": policy["authority"],
        "approval_status": policy["approval_status"],
        "status": statuses["ready"],
        "index_status": index_statuses["pending"],
        "revision": policy["initial_revision"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await requirement_document_repository.insert(document)
    except DuplicateKeyError:
        existing = await requirement_document_repository.find_by_hash(
            project_id, content_hash
        )
        if existing:
            return existing
        raise
    await audit(
        user.id,
        policy["events"]["created"],
        policy["entity_type"],
        document["_id"],
        project_id,
        {"content_hash": content_hash, "format": payload.format},
    )
    indexed = await index_artifact(
        project_id,
        policy["artifact_type"],
        document["_id"],
        document["_id"],
        document["filename"],
        content,
        document["status"],
        document["authority"],
        document["source_version"],
    )
    document["index_status"] = (
        index_statuses["indexed"] if indexed else index_statuses["failed"]
    )
    document["indexed_at"] = now()
    await requirement_document_repository.set_index_result(
        document["_id"],
        project_id,
        document["index_status"],
        document["indexed_at"],
    )
    return document


async def store_raw_requirement_source(project_id, document_id, filename, content_type, data):
    return await storage_client.store_requirement_source(
        project_id, document_id, filename, content_type, data
    )


async def read_raw_requirement_source(document):
    policy = DOCUMENT_POLICY
    source = document.get("raw_source") or {}
    if source.get("storage") == policy["embedded_storage"]:
        content = serialized_content(source.get("content"))
        return content.encode("utf-8")
    object_key = source.get("object_key")
    if not object_key:
        raise HTTPException(
            status_code=409,
            detail={"code": policy["error_codes"]["raw_source_unavailable"]},
        )
    return await storage_client.read_requirement_source(
        document["project_id"], document["_id"], object_key
    )


async def index_requirement_document(document):
    policy = DOCUMENT_POLICY
    statuses = policy["statuses"]
    indexed = await index_artifact(
        document["project_id"],
        policy["artifact_type"],
        document["_id"],
        document["_id"],
        document.get("title") or document.get("filename") or document["_id"],
        serialized_content(document.get("normalized_content") or ""),
        document.get("status", statuses["ready"]),
        document.get("authority", policy["authority"]),
        document.get("source_version", policy["source_version"]),
        module=document.get("module", ""),
        component=document.get("component"),
        product_area=document.get("product_area"),
        release_id=document.get("release_id"),
        external_source_id=document.get("external_source_id"),
        approval_status=document.get("approval_status", policy["approval_status"]),
        owner_id=document.get("owner_id"),
        approved_by=document.get("approved_by"),
        approved_at=document.get("approved_at"),
        effective_from=document.get("effective_from"),
        tags=document.get("tags", []),
    )
    await requirement_document_repository.set_index_result(
        document["_id"],
        document["project_id"],
        policy["index_statuses"]["indexed"]
        if indexed
        else policy["index_statuses"]["failed"],
        now(),
    )
    return indexed


async def upload_requirement_document_record(
    project_id,
    format,
    filename,
    content_type,
    data,
    user,
):
    policy = DOCUMENT_POLICY
    statuses = policy["statuses"]
    index_statuses = policy["index_statuses"]
    result_statuses = policy["result_statuses"]
    degraded_modes = policy["degraded_modes"]
    codes = policy["error_codes"]
    if format not in supported_requirement_formats():
        raise HTTPException(status_code=422, detail={"code": codes["unsupported_format"]})
    if not data:
        raise HTTPException(status_code=422, detail={"code": codes["empty_import"]})
    if len(data) > settings.MAX_REQUIREMENT_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail={"code": codes["import_too_large"]})
    await get_project(project_id, user, policy["permissions"]["upload"])
    resolved_filename = filename or f"{policy['default_filename_prefix']}.{format}"
    content_hash = hashlib.sha256(data).hexdigest()
    existing = await requirement_document_repository.find_by_hash(project_id, content_hash)
    if existing:
        return RequirementDocumentResult(existing)
    document_id = new_id(policy["id_prefix"])
    source = await store_raw_requirement_source(
        project_id,
        document_id,
        resolved_filename,
        content_type,
        data,
    )
    timestamp = now()
    document = {
        "_id": document_id,
        "project_id": project_id,
        "filename": resolved_filename,
        "format": format,
        "content_hash": source["sha256"],
        "raw_source": source,
        "normalized_content": None,
        "source_version": policy["source_version"],
        "source_type": policy["source_type"],
        "authority": policy["authority"],
        "approval_status": policy["approval_status"],
        "status": statuses["uploaded"],
        "index_status": index_statuses["pending"],
        "revision": policy["initial_revision"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await requirement_document_repository.insert(document)
    except DuplicateKeyError:
        existing = await requirement_document_repository.find_by_hash(
            project_id, content_hash
        )
        if existing:
            return RequirementDocumentResult(existing)
        raise
    await audit(
        user.id,
        policy["events"]["uploaded"],
        policy["entity_type"],
        document_id,
        project_id,
        {
            "content_hash": source["sha256"],
            "object_key": source["object_key"],
            "format": format,
        },
    )
    try:
        content = extract_file_content(data, format)
    except Exception as error:
        await requirement_document_repository.update(
            document_id,
            project_id,
            {
                "status": statuses["parse_failed"],
                "parse_error_type": type(error).__name__,
                "updated_at": now(),
            },
            increment_revision=True,
        )
        document = await requirement_document_repository.find(document_id, project_id)
        await audit(
            user.id,
            policy["events"]["parse_failed"],
            policy["entity_type"],
            document_id,
            project_id,
            {"error_type": type(error).__name__},
        )
        return RequirementDocumentResult(
            document, result_statuses["degraded"], degraded_modes["parser"]
        )
    normalized = serialized_content(content)
    await requirement_document_repository.update(
        document_id,
        project_id,
        {
            "normalized_content": content,
            "normalized_content_hash": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
            "status": statuses["ready"],
            "updated_at": now(),
        },
        increment_revision=True,
    )
    document = await requirement_document_repository.find(document_id, project_id)
    indexed = await index_requirement_document(document)
    document = await requirement_document_repository.find(document_id, project_id)
    return RequirementDocumentResult(
        document,
        result_statuses["success"] if indexed else result_statuses["degraded"],
        None if indexed else degraded_modes["vector"],
    )


async def list_requirement_document_records(project_id, status, query_text, limit, user):
    await get_project(project_id, user, DOCUMENT_POLICY["permissions"]["read"])
    query = {"project_id": project_id}
    if status:
        query["status"] = status.upper()
    if query_text:
        query["filename"] = {"$regex": re.escape(query_text), "$options": "i"}
    return await requirement_document_repository.list(query, limit)


async def get_requirement_document_record(document_id, user, permission=None):
    policy = DOCUMENT_POLICY
    return await get_project_entity(
        policy["collection"],
        document_id,
        user,
        permission or policy["permissions"]["read"],
    )


async def update_requirement_document_record(document_id, payload, user):
    policy = DOCUMENT_POLICY
    result_statuses = policy["result_statuses"]
    degraded_modes = policy["degraded_modes"]
    codes = policy["error_codes"]
    document = await get_requirement_document_record(
        document_id, user, policy["permissions"]["manage"]
    )
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    resulting = {**document, **changes}
    if resulting.get("approval_status") == policy["statuses"]["approved"] and (
        not resulting.get("approved_by") or not resulting.get("approved_at")
    ):
        raise HTTPException(
            status_code=422,
            detail={"code": codes["approval_provenance_required"]},
        )
    if changes.get("release_id"):
        if not await requirement_document_repository.release_exists(
            document["project_id"], changes["release_id"]
        ):
            raise HTTPException(status_code=422, detail={"code": codes["invalid_release"]})
    changes["index_status"] = policy["index_statuses"]["pending"]
    updated = await requirement_document_repository.update_with_revision(
        document_id,
        document["project_id"],
        payload.expected_revision,
        {**changes, "updated_at": now()},
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": codes["revision_conflict"]})
    indexed = await index_requirement_document(updated)
    updated = await requirement_document_repository.find(
        document_id, document["project_id"]
    )
    await audit(
        user.id,
        policy["events"]["metadata_updated"],
        policy["entity_type"],
        document_id,
        document["project_id"],
        {"fields": sorted(changes)},
    )
    return RequirementDocumentResult(
        updated,
        result_statuses["success"] if indexed else result_statuses["degraded"],
        None if indexed else degraded_modes["vector"],
    )


async def reindex_requirement_document_record(document_id, user):
    policy = DOCUMENT_POLICY
    result_statuses = policy["result_statuses"]
    degraded_modes = policy["degraded_modes"]
    document = await get_requirement_document_record(
        document_id, user, policy["permissions"]["manage"]
    )
    if document.get("status") == policy["statuses"]["archived"]:
        raise HTTPException(
            status_code=409,
            detail={"code": policy["error_codes"]["document_archived"]},
        )
    indexed = await index_requirement_document(document)
    await requirement_document_repository.update(
        document_id,
        document["project_id"],
        {"updated_at": now()},
        increment_revision=True,
    )
    updated = await requirement_document_repository.find(
        document_id, document["project_id"]
    )
    await audit(
        user.id,
        policy["events"]["reindexed"],
        policy["entity_type"],
        document_id,
        document["project_id"],
        {"indexed": indexed},
    )
    return RequirementDocumentResult(
        updated,
        result_statuses["success"] if indexed else result_statuses["degraded"],
        None if indexed else degraded_modes["vector"],
    )


async def archive_requirement_document_record(document_id, payload, user):
    policy = DOCUMENT_POLICY
    statuses = policy["statuses"]
    document = await get_requirement_document_record(
        document_id, user, policy["permissions"]["archive"]
    )
    if document.get("status") == statuses["archived"]:
        return document
    timestamp = now()
    updated = await requirement_document_repository.update_with_revision(
        document_id,
        document["project_id"],
        payload.expected_revision,
        {
            "status_before_archive": document.get("status", statuses["ready"]),
            "status": statuses["archived"],
            "archived_by": user.id,
            "archived_at": timestamp,
            "archive_reason": payload.reason,
            "updated_at": timestamp,
        },
    )
    if not updated:
        raise HTTPException(
            status_code=409,
            detail={"code": policy["error_codes"]["revision_conflict"]},
        )
    await audit(
        user.id,
        policy["events"]["archived"],
        policy["entity_type"],
        document_id,
        document["project_id"],
        {"reason": payload.reason},
    )
    return updated


async def restore_requirement_document_record(document_id, payload, user):
    policy = DOCUMENT_POLICY
    statuses = policy["statuses"]
    document = await get_requirement_document_record(
        document_id, user, policy["permissions"]["restore"]
    )
    if document.get("status") != statuses["archived"]:
        return document
    timestamp = now()
    updated = await requirement_document_repository.update_with_revision(
        document_id,
        document["project_id"],
        payload.expected_revision,
        {
            "status": document.get("status_before_archive", statuses["ready"]),
            "restored_by": user.id,
            "restored_at": timestamp,
            "restore_reason": payload.reason,
            "updated_at": timestamp,
        },
        status=statuses["archived"],
    )
    if not updated:
        raise HTTPException(
            status_code=409,
            detail={"code": policy["error_codes"]["revision_conflict"]},
        )
    await audit(
        user.id,
        policy["events"]["restored"],
        policy["entity_type"],
        document_id,
        document["project_id"],
        {"reason": payload.reason},
    )
    return updated


async def retry_requirement_document_parse_record(document_id, payload, user):
    policy = DOCUMENT_POLICY
    statuses = policy["statuses"]
    result_statuses = policy["result_statuses"]
    degraded_modes = policy["degraded_modes"]
    codes = policy["error_codes"]
    document = await get_requirement_document_record(
        document_id, user, policy["permissions"]["extract"]
    )
    if document.get("status") == statuses["ready"]:
        return RequirementDocumentResult(document)
    if document.get("status") != statuses["parse_failed"]:
        raise HTTPException(
            status_code=409,
            detail={"code": codes["document_not_retryable"], "status": document.get("status")},
        )
    claimed = await requirement_document_repository.claim_status(
        document_id,
        document["project_id"],
        statuses["parse_failed"],
        payload.expected_revision,
        statuses["parsing"],
        now(),
    )
    if claimed.matched_count != 1:
        raise HTTPException(status_code=409, detail={"code": codes["revision_conflict"]})
    try:
        data = await read_raw_requirement_source(document)
        content = extract_file_content(data, document["format"])
    except Exception as error:
        await requirement_document_repository.transition_status(
            document_id,
            document["project_id"],
            statuses["parsing"],
            {
                "status": statuses["parse_failed"],
                "parse_error_type": type(error).__name__,
                "updated_at": now(),
            },
        )
        failed = await requirement_document_repository.find(
            document_id, document["project_id"]
        )
        await audit(
            user.id,
            policy["events"]["parse_retry_failed"],
            policy["entity_type"],
            document_id,
            document["project_id"],
            {"error_type": type(error).__name__},
        )
        return RequirementDocumentResult(
            failed, result_statuses["degraded"], degraded_modes["parser"]
        )
    normalized = serialized_content(content)
    updated = await requirement_document_repository.transition_status(
        document_id,
        document["project_id"],
        statuses["parsing"],
        {
            "normalized_content": content,
            "normalized_content_hash": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
            "status": statuses["ready"],
            "parse_error_type": None,
            "updated_at": now(),
        },
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": codes["parse_retry_conflict"]})
    await audit(
        user.id,
        policy["events"]["parse_retry_succeeded"],
        policy["entity_type"],
        document_id,
        document["project_id"],
    )
    return RequirementDocumentResult(updated)
