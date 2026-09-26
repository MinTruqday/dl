import hashlib
import re
from dataclasses import dataclass

from fastapi import HTTPException

from src.core.common import audit, get_project, get_project_entity, new_id, now, require_action_policy
from src.repositories.requirement_document import requirement_document_repository
from src.clients.project_knowledge import index_artifact
from src.services.domain_policy import domain_policy


SOURCE_POLICY = domain_policy("requirement_source")


@dataclass(frozen=True)
class RequirementSourceResult:
    data: dict
    indexed: bool

    @property
    def status(self):
        return (
            SOURCE_POLICY["success_result_status"]
            if self.indexed
            else SOURCE_POLICY["degraded_result_status"]
        )

    @property
    def degraded_mode(self):
        return None if self.indexed else SOURCE_POLICY["vector_degraded_mode"]


async def create_requirement_source(project_id, payload, user):
    await get_project(project_id, user, SOURCE_POLICY["manage_permission"])
    content_hash = hashlib.sha256(payload.content.encode("utf-8")).hexdigest()
    existing = await requirement_document_repository.find_by_hash(project_id, content_hash)
    if existing:
        return RequirementSourceResult(
            existing, existing.get("index_status") == SOURCE_POLICY["indexed_status"]
        )
    timestamp = now()
    safe_name = (
        re.sub(
            SOURCE_POLICY["filename_pattern"],
            SOURCE_POLICY["filename_replacement"],
            payload.title,
        ).strip(SOURCE_POLICY["filename_replacement"])
        or SOURCE_POLICY["fallback_filename"]
    )
    document = {
        "_id": new_id(SOURCE_POLICY["id_prefix"]),
        "project_id": project_id,
        "filename": f"{safe_name}{SOURCE_POLICY['file_extension']}",
        "format": SOURCE_POLICY["file_format"],
        "content_hash": content_hash,
        "raw_source": {
            "storage": SOURCE_POLICY["storage_type"],
            "content": payload.content,
            "sha256": content_hash,
            "size": len(payload.content.encode("utf-8")),
            "source_url": payload.source_url,
        },
        "normalized_content": payload.content,
        "normalized_content_hash": content_hash,
        "source_version": payload.source_version,
        "title": payload.title,
        "source_type": payload.source_type,
        "authority": payload.authority,
        "source_url": payload.source_url,
        "owner_id": payload.owner_id,
        "module": payload.module,
        "component": payload.component,
        "product_area": payload.product_area,
        "release_id": payload.release_id,
        "external_source_id": payload.external_source_id,
        "approval_status": payload.approval_status,
        "approved_by": payload.approved_by,
        "approved_at": payload.approved_at,
        "effective_from": payload.effective_from,
        "tags": payload.tags,
        "status": SOURCE_POLICY["ready_status"],
        "index_status": SOURCE_POLICY["pending_index_status"],
        "revision": SOURCE_POLICY["initial_revision"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    await requirement_document_repository.insert(document)
    indexed = await index_artifact(
        project_id,
        "requirement_document",
        document["_id"],
        document["_id"],
        payload.title,
        payload.content,
        document["status"],
        payload.authority,
        payload.source_version,
        module=payload.module or "",
        component=payload.component,
        product_area=payload.product_area,
        release_id=payload.release_id,
        external_source_id=payload.external_source_id,
        approval_status=payload.approval_status,
        owner_id=payload.owner_id,
        approved_by=payload.approved_by,
        approved_at=payload.approved_at,
        effective_from=payload.effective_from,
        tags=payload.tags,
    )
    document["index_status"] = (
        SOURCE_POLICY["indexed_status"] if indexed else SOURCE_POLICY["failed_index_status"]
    )
    document["indexed_at"] = now()
    await requirement_document_repository.set_index_result(
        document["_id"], project_id, document["index_status"], document["indexed_at"]
    )
    await audit(
        user.id,
        SOURCE_POLICY["created_event"],
        SOURCE_POLICY["entity"],
        document["_id"],
        project_id,
        {"source_type": payload.source_type, "authority": payload.authority},
    )
    return RequirementSourceResult(document, indexed)


async def list_requirement_sources(project_id, include_archived, user):
    await get_project(project_id, user, SOURCE_POLICY["read_permission"])
    query = {"project_id": project_id}
    if not include_archived:
        query["status"] = {"$ne": SOURCE_POLICY["archived_status"]}
    documents = await requirement_document_repository.list(query, SOURCE_POLICY["list_limit"])
    project = await requirement_document_repository.project_authority_order(project_id)
    order = (project or {}).get("settings", {}).get(
        "knowledge_authority_order", SOURCE_POLICY["default_authority_order"]
    )
    ranks = {value: index for index, value in enumerate(order)}
    documents.sort(
        key=lambda item: (ranks.get(item.get("authority"), len(ranks)), item.get("updated_at"))
    )
    return documents


async def reindex_requirement_source(document_id, user):
    document = await get_project_entity(
        SOURCE_POLICY["collection"],
        document_id,
        user,
        SOURCE_POLICY["manage_permission"],
    )
    if document.get("status") == SOURCE_POLICY["archived_status"]:
        raise HTTPException(
            status_code=409, detail={"code": SOURCE_POLICY["archived_code"]}
        )
    content = str((document.get("raw_source") or {}).get("content") or "")
    indexed = await index_artifact(
        document["project_id"],
        "requirement_document",
        document["_id"],
        document["_id"],
        document.get("title") or document.get("filename") or "",
        content,
        document.get("status", SOURCE_POLICY["ready_status"]),
        document.get("authority"),
        document.get("source_version"),
        module=document.get("module") or "",
        component=document.get("component"),
        product_area=document.get("product_area"),
        release_id=document.get("release_id"),
        external_source_id=document.get("external_source_id"),
        approval_status=document.get("approval_status"),
        owner_id=document.get("owner_id"),
        approved_by=document.get("approved_by"),
        approved_at=document.get("approved_at"),
        effective_from=document.get("effective_from"),
        tags=document.get("tags", []),
    )
    timestamp = now()
    await requirement_document_repository.set_index_result(
        document_id,
        document["project_id"],
        SOURCE_POLICY["indexed_status"]
        if indexed
        else SOURCE_POLICY["failed_index_status"],
        timestamp,
    )
    await requirement_document_repository.update(
        document_id,
        document["project_id"],
        {"updated_at": timestamp},
        increment_revision=True,
    )
    updated = await requirement_document_repository.find(
        document_id, document["project_id"]
    )
    await audit(
        user.id,
        SOURCE_POLICY["reindexed_event"],
        SOURCE_POLICY["entity"],
        document_id,
        document["project_id"],
        {"indexed": indexed},
    )
    return RequirementSourceResult(updated, indexed)


async def archive_requirement_source(document_id, payload, user):
    document = await get_project_entity(
        SOURCE_POLICY["collection"], document_id, user, SOURCE_POLICY["manage_permission"]
    )
    await require_action_policy(
        document["project_id"],
        user,
        SOURCE_POLICY["archive_permission"],
        set(SOURCE_POLICY["archive_roles"]),
    )
    if document.get("status") == SOURCE_POLICY["archived_status"]:
        return document
    timestamp = now()
    updated = await requirement_document_repository.update_with_revision(
        document_id,
        document["project_id"],
        payload.expected_revision,
        {
            "status_before_archive": document.get("status", SOURCE_POLICY["ready_status"]),
            "status": SOURCE_POLICY["archived_status"],
            "archived_by": user.id,
            "archived_at": timestamp,
            "archive_reason": payload.reason,
            "updated_at": timestamp,
        },
    )
    if not updated:
        raise HTTPException(
            status_code=409, detail={"code": SOURCE_POLICY["revision_conflict_code"]}
        )
    await audit(
        user.id,
        SOURCE_POLICY["archived_event"],
        SOURCE_POLICY["entity"],
        document_id,
        document["project_id"],
        {"reason": payload.reason},
    )
    return updated
