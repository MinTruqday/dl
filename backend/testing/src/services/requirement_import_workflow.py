from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, get_project_entity, new_id, now, validate_doc
from src.domain.contracts import RequirementCreate
from src.repositories.requirement_import import requirement_import_repository
from src.services.domain_policy import domain_policy
from src.services.requirement_import import atomic_requirement_candidates, parse_requirement_import
from src.services.requirement_indexing import validate_requirement_sources
from src.services.requirement_records import create_requirement_record
from src.services.requirement_transformations import unique_source_refs
from src.services.requirement_workflow import (
    candidate_fingerprint,
    prepare_requirement_candidates,
)

IMPORT_POLICY = domain_policy("requirement_import")


async def extract_requirement_candidates(document_id, payload, user):
    policy = IMPORT_POLICY
    document = await get_project_entity(
        policy["document_collection"],
        document_id,
        user,
        policy["permissions"]["extract"],
    )
    if document.get("status") == policy["archived_document_status"]:
        raise HTTPException(
            status_code=409, detail={"code": policy["error_codes"]["document_archived"]}
        )
    if document.get("normalized_content") is None:
        raise HTTPException(
            status_code=409,
            detail={
                "code": policy["error_codes"]["document_parse_required"],
                "status": document.get("status"),
            },
        )
    existing = await requirement_import_repository.find_by_source_document(document_id)
    if existing:
        return existing
    await audit(
        user.id,
        policy["events"]["extraction_requested"],
        policy["document_entity_type"],
        document_id,
        document["project_id"],
    )
    job_id = new_id(policy["job_id_prefix"])
    candidates = prepare_requirement_candidates(job_id, atomic_requirement_candidates(document))
    job = {
        "_id": job_id,
        "project_id": document["project_id"],
        "source_document_id": document_id,
        "source_content_hash": document["content_hash"],
        "filename": document["filename"],
        "format": document["format"],
        "status": policy["preview_status"],
        "preview": candidates,
        "candidate_count": len(candidates),
        "extraction_mode": policy["deterministic_mode"],
        "idempotency_key": payload.idempotency_key,
        "revision": policy["initial_revision"],
        "created_by": user.id,
        "created_at": now(),
    }
    try:
        await requirement_import_repository.insert(job)
    except DuplicateKeyError:
        return await requirement_import_repository.find_by_source_document(document_id)
    await requirement_import_repository.mark_document_extracted(
        document_id,
        document["project_id"],
        policy["extracted_document_status"],
        job["_id"],
        now(),
    )
    await audit(
        user.id,
        policy["events"]["extraction_completed"],
        policy["document_entity_type"],
        document_id,
        document["project_id"],
        {"job_id": job["_id"], "candidate_count": len(candidates)},
    )
    return job


async def create_requirement_import_job(project_id, payload, user):
    policy = IMPORT_POLICY
    await get_project(project_id, user, policy["permissions"]["requirement_create"])
    job_id = new_id(policy["job_id_prefix"])
    previews = prepare_requirement_candidates(
        job_id,
        parse_requirement_import(payload.content, payload.format),
    )
    job = {
        "_id": job_id,
        "project_id": project_id,
        "filename": payload.filename,
        "format": payload.format,
        "status": policy["preview_status"],
        "preview": previews,
        "candidate_count": len(previews),
        "revision": policy["initial_revision"],
        "created_by": user.id,
        "created_at": now(),
    }
    await requirement_import_repository.insert(job)
    await audit(
        user.id,
        policy["events"]["previewed"],
        policy["job_entity_type"],
        job["_id"],
        project_id,
        {"count": len(previews)},
    )
    return job


async def review_requirement_import_job(job_id, payload, user):
    policy = IMPORT_POLICY
    job = await get_project_entity(
        policy["job_collection"], job_id, user, policy["permissions"]["review"]
    )
    if job.get("status") != policy["preview_status"]:
        raise HTTPException(
            status_code=409,
            detail={
                "code": policy["error_codes"]["preview_not_editable"],
                "status": job.get("status"),
            },
        )
    current_preview = prepare_requirement_candidates(job_id, job.get("preview", []))
    submitted = [candidate.model_dump() for candidate in payload.preview]
    if len(submitted) == len(current_preview) and all(
        not item.get("candidate_id") for item in submitted
    ):
        for index, item in enumerate(submitted):
            item["candidate_id"] = current_preview[index]["candidate_id"]
    current_by_id = {item["candidate_id"]: item for item in current_preview}
    submitted_by_id = {item.get("candidate_id"): item for item in submitted}
    if None in submitted_by_id or set(submitted_by_id) != set(current_by_id):
        raise HTTPException(
            status_code=422, detail={"code": policy["error_codes"]["candidate_set_changed"]}
        )
    preview = []
    for current in current_preview:
        candidate = submitted_by_id[current["candidate_id"]]
        candidate["source_refs"] = current.get("source_refs", [])
        candidate["candidate_status"] = policy["active_candidate_status"]
        candidate["candidate_revision"] = int(current.get("candidate_revision", 1)) + 1
        candidate["candidate_relation"] = current.get("candidate_relation")
        candidate["parent_candidate_ids"] = current.get("parent_candidate_ids", [])
        preview.append(candidate)
        validate_doc(candidate["content_doc"])
        for criterion in candidate.get("acceptance_criteria", []):
            validate_doc(criterion["content_doc"])
    updated = await requirement_import_repository.update_preview(
        job_id,
        job["project_id"],
        policy["preview_status"],
        payload.expected_revision,
        preview,
        user.id,
        now(),
        review_note=payload.review_note,
    )
    if not updated:
        raise HTTPException(
            status_code=409, detail={"code": policy["error_codes"]["revision_conflict"]}
        )
    await audit(
        user.id,
        policy["events"]["reviewed"],
        policy["job_entity_type"],
        job_id,
        job["project_id"],
        {"candidate_count": len(preview), "review_note": payload.review_note},
    )
    return updated


async def merge_requirement_import_candidates(job_id, payload, user):
    policy = IMPORT_POLICY
    job = await get_project_entity(
        policy["job_collection"], job_id, user, policy["permissions"]["review"]
    )
    if job.get("status") != policy["preview_status"]:
        raise HTTPException(
            status_code=409, detail={"code": policy["error_codes"]["preview_not_editable"]}
        )
    candidate_ids = list(dict.fromkeys(payload.candidate_ids))
    if len(candidate_ids) != len(payload.candidate_ids):
        raise HTTPException(
            status_code=422, detail={"code": policy["error_codes"]["duplicate_candidate"]}
        )
    preview = prepare_requirement_candidates(job_id, job.get("preview", []))
    by_id = {item["candidate_id"]: item for item in preview}
    if not set(candidate_ids) <= set(by_id):
        raise HTTPException(
            status_code=404, detail={"code": policy["error_codes"]["candidate_not_found"]}
        )
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
    merged_id = new_id(policy["candidate_id_prefix"])
    merged.update(
        {
            "candidate_id": merged_id,
            "candidate_status": policy["active_candidate_status"],
            "candidate_revision": policy["initial_revision"],
            "candidate_relation": policy["merged_relation"],
            "parent_candidate_ids": candidate_ids,
            "extraction_confidence": min(
                (float(item.get("extraction_confidence", 1)) for item in parents),
                default=1,
            ),
        }
    )
    first_index = min(
        index for index, item in enumerate(preview) if item["candidate_id"] in candidate_ids
    )
    next_preview = [item for item in preview if item["candidate_id"] not in candidate_ids]
    next_preview.insert(first_index, merged)
    event = {
        "_id": new_id(policy["operation_id_prefix"]),
        "type": policy["merge_operation"],
        "parent_candidate_ids": candidate_ids,
        "result_candidate_ids": [merged_id],
        "parent_fingerprints": [candidate_fingerprint(item) for item in parents],
        "source_refs": merged["source_refs"],
        "reason": payload.reason,
        "actor_id": user.id,
        "created_at": now(),
    }
    updated = await requirement_import_repository.update_preview(
        job_id,
        job["project_id"],
        policy["preview_status"],
        payload.expected_revision,
        next_preview,
        user.id,
        now(),
        push_field="candidate_lineage",
        push_value=event,
    )
    if not updated:
        raise HTTPException(
            status_code=409, detail={"code": policy["error_codes"]["revision_conflict"]}
        )
    await audit(
        user.id,
        policy["events"]["merged"],
        policy["job_entity_type"],
        job_id,
        job["project_id"],
        {
            "parent_candidate_ids": candidate_ids,
            "result_candidate_id": merged_id,
            "reason": payload.reason,
        },
    )
    return updated


async def split_requirement_import_candidate(job_id, candidate_id, payload, user):
    policy = IMPORT_POLICY
    job = await get_project_entity(
        policy["job_collection"], job_id, user, policy["permissions"]["review"]
    )
    if job.get("status") != policy["preview_status"]:
        raise HTTPException(
            status_code=409, detail={"code": policy["error_codes"]["preview_not_editable"]}
        )
    preview = prepare_requirement_candidates(job_id, job.get("preview", []))
    parent = next((item for item in preview if item["candidate_id"] == candidate_id), None)
    if not parent:
        raise HTTPException(
            status_code=404, detail={"code": policy["error_codes"]["candidate_not_found"]}
        )
    if len(preview) - 1 + len(payload.drafts) > policy["candidate_limit"]:
        raise HTTPException(
            status_code=422, detail={"code": policy["error_codes"]["candidate_limit"]}
        )
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
                "candidate_id": new_id(policy["candidate_id_prefix"]),
                "candidate_status": policy["active_candidate_status"],
                "candidate_revision": policy["initial_revision"],
                "candidate_relation": f"{policy['split_relation_prefix']}-{index + 1}",
                "parent_candidate_ids": [candidate_id],
                "extraction_confidence": float(parent.get("extraction_confidence", 1)),
            }
        )
        children.append(child)
    parent_index = next(
        index for index, item in enumerate(preview) if item["candidate_id"] == candidate_id
    )
    next_preview = list(preview)
    next_preview[parent_index : parent_index + 1] = children
    event = {
        "_id": new_id(policy["operation_id_prefix"]),
        "type": policy["split_operation"],
        "parent_candidate_ids": [candidate_id],
        "result_candidate_ids": [item["candidate_id"] for item in children],
        "parent_fingerprints": [candidate_fingerprint(parent)],
        "source_refs": parent.get("source_refs", []),
        "reason": payload.reason,
        "actor_id": user.id,
        "created_at": now(),
    }
    updated = await requirement_import_repository.update_preview(
        job_id,
        job["project_id"],
        policy["preview_status"],
        payload.expected_revision,
        next_preview,
        user.id,
        now(),
        push_field="candidate_lineage",
        push_value=event,
    )
    if not updated:
        raise HTTPException(
            status_code=409, detail={"code": policy["error_codes"]["revision_conflict"]}
        )
    await audit(
        user.id,
        policy["events"]["split"],
        policy["job_entity_type"],
        job_id,
        job["project_id"],
        {
            "parent_candidate_id": candidate_id,
            "result_candidate_ids": [item["candidate_id"] for item in children],
            "reason": payload.reason,
        },
    )
    return updated


async def reject_requirement_import_candidate(job_id, candidate_id, payload, user):
    policy = IMPORT_POLICY
    job = await get_project_entity(
        policy["job_collection"], job_id, user, policy["permissions"]["review"]
    )
    if job.get("status") != policy["preview_status"]:
        raise HTTPException(
            status_code=409, detail={"code": policy["error_codes"]["preview_not_editable"]}
        )
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
            return job
        raise HTTPException(
            status_code=404, detail={"code": policy["error_codes"]["candidate_not_found"]}
        )
    rejected = {
        **candidate,
        "candidate_status": policy["rejected_candidate_status"],
        "candidate_revision": int(candidate.get("candidate_revision", 1)) + 1,
        "rejection_reason": payload.reason,
        "rejected_by": user.id,
        "rejected_at": now(),
    }
    next_preview = [item for item in preview if item["candidate_id"] != candidate_id]
    updated = await requirement_import_repository.update_preview(
        job_id,
        job["project_id"],
        policy["preview_status"],
        payload.expected_revision,
        next_preview,
        user.id,
        now(),
        push_field="rejected_candidates",
        push_value=rejected,
    )
    if not updated:
        raise HTTPException(
            status_code=409, detail={"code": policy["error_codes"]["revision_conflict"]}
        )
    await audit(
        user.id,
        policy["events"]["rejected"],
        policy["job_entity_type"],
        job_id,
        job["project_id"],
        {"candidate_id": candidate_id, "reason": payload.reason},
    )
    return updated


async def confirm_requirement_import_job(job_id, payload, user):
    policy = IMPORT_POLICY
    job = await get_project_entity(
        policy["job_collection"], job_id, user, policy["permissions"]["confirm"]
    )
    await get_project(job["project_id"], user, policy["permissions"]["requirement_create"])
    if job["status"] == policy["confirmed_status"]:
        return {"job": job, "requirements": None}
    indexes = payload.selected_indexes or list(range(len(job["preview"])))
    indexes = list(dict.fromkeys(indexes))
    for index in indexes:
        if index < 0 or index >= len(job["preview"]):
            raise HTTPException(
                status_code=422,
                detail={"code": policy["error_codes"]["invalid_preview_index"]},
            )
    claimed = await requirement_import_repository.claim_confirmation(
        job_id,
        job["project_id"],
        policy["preview_status"],
        policy["confirming_status"],
        user.id,
        now(),
        payload.expected_revision,
    )
    if not claimed:
        current = await requirement_import_repository.find(job_id, job["project_id"])
        if current and current.get("status") == policy["confirmed_status"]:
            return {"job": current, "requirements": None}
        raise HTTPException(
            status_code=409,
            detail={"code": policy["error_codes"]["confirmation_in_progress"]},
        )
    created = []
    try:
        for index in indexes:
            item = job["preview"][index]
            created.append(
                await create_requirement_record(
                    job["project_id"],
                    RequirementCreate(**item),
                    user,
                    origin=policy["import_origin"],
                )
            )
    except Exception:
        requirement_ids = [item["_id"] for item in created]
        version_ids = [item["current_version"]["_id"] for item in created]
        await requirement_import_repository.delete_created_requirements(
            requirement_ids, version_ids
        )
        await requirement_import_repository.reset_confirmation(
            job_id,
            job["project_id"],
            policy["confirming_status"],
            policy["preview_status"],
            now(),
        )
        await audit(
            user.id,
            policy["events"]["confirmation_failed"],
            policy["job_entity_type"],
            job_id,
            job["project_id"],
        )
        raise
    rejected_indexes = [index for index in range(len(job["preview"])) if index not in indexes]
    await requirement_import_repository.confirm(
        job_id,
        job["project_id"],
        policy["confirming_status"],
        policy["confirmed_status"],
        [item["_id"] for item in created],
        indexes,
        rejected_indexes,
        user.id,
        now(),
    )
    if job.get("source_document_id"):
        await requirement_import_repository.confirm_document(
            job["source_document_id"],
            job["project_id"],
            policy["confirmed_status"],
            now(),
        )
    await audit(
        user.id,
        policy["events"]["confirmed"],
        policy["job_entity_type"],
        job_id,
        job["project_id"],
        {
            "created_requirement_ids": [item["_id"] for item in created],
            "selected_indexes": indexes,
            "rejected_indexes": rejected_indexes,
        },
    )
    return {"job": None, "requirements": created}
