from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, get_project_entity, new_id, now, validate_doc
from src.schemas.contracts.requirements import RequirementCreate
from src.repositories.requirement_import import requirement_import_repository
from src.modules.requirements.services.requirement_import import atomic_requirement_candidates, parse_requirement_import
from src.modules.requirements.services.requirement_indexing import validate_requirement_sources
from src.modules.requirements.services.requirement_records import create_requirement_record
from src.modules.requirements.services.requirement_transformations import unique_source_refs
from src.modules.requirements.services.requirement_workflow import (
    candidate_fingerprint,
    prepare_requirement_candidates,
)




async def extract_requirement_candidates(document_id, payload, user):
    
    document = await get_project_entity(
        'requirement_documents',
        document_id,
        user,
        'requirement_document.extract',
    )
    if document.get("status") == 'ARCHIVED':
        raise HTTPException(
            status_code=409, detail={"code": 'DOCUMENT_ARCHIVED'}
        )
    if document.get("normalized_content") is None:
        raise HTTPException(
            status_code=409,
            detail={
                "code": 'DOCUMENT_PARSE_REQUIRED',
                "status": document.get("status"),
            },
        )
    existing = await requirement_import_repository.find_by_source_document(document_id)
    if existing:
        return existing
    await audit(
        user.id,
        'requirement_extraction_requested',
        'RequirementDocument',
        document_id,
        document["project_id"],
    )
    job_id = new_id('RIMP')
    candidates = prepare_requirement_candidates(job_id, atomic_requirement_candidates(document))
    job = {
        "_id": job_id,
        "project_id": document["project_id"],
        "source_document_id": document_id,
        "source_content_hash": document["content_hash"],
        "filename": document["filename"],
        "format": document["format"],
        "status": 'PREVIEW_READY',
        "preview": candidates,
        "candidate_count": len(candidates),
        "extraction_mode": 'DETERMINISTIC',
        "idempotency_key": payload.idempotency_key,
        "revision": 1,
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
        'EXTRACTED',
        job["_id"],
        now(),
    )
    await audit(
        user.id,
        'requirement_extraction_completed',
        'RequirementDocument',
        document_id,
        document["project_id"],
        {"job_id": job["_id"], "candidate_count": len(candidates)},
    )
    return job


async def create_requirement_import_job(project_id, payload, user):
    
    await get_project(project_id, user, 'requirement.create')
    job_id = new_id('RIMP')
    previews = prepare_requirement_candidates(
        job_id,
        parse_requirement_import(payload.content, payload.format),
    )
    job = {
        "_id": job_id,
        "project_id": project_id,
        "filename": payload.filename,
        "format": payload.format,
        "status": 'PREVIEW_READY',
        "preview": previews,
        "candidate_count": len(previews),
        "revision": 1,
        "created_by": user.id,
        "created_at": now(),
    }
    await requirement_import_repository.insert(job)
    await audit(
        user.id,
        'requirement_import_previewed',
        'RequirementImport',
        job["_id"],
        project_id,
        {"count": len(previews)},
    )
    return job


async def review_requirement_import_job(job_id, payload, user):
    
    job = await get_project_entity(
        'import_jobs', job_id, user, 'requirement_document.review_extraction'
    )
    if job.get("status") != 'PREVIEW_READY':
        raise HTTPException(
            status_code=409,
            detail={
                "code": 'IMPORT_PREVIEW_NOT_EDITABLE',
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
            status_code=422, detail={"code": 'CANDIDATE_SET_CHANGED'}
        )
    preview = []
    for current in current_preview:
        candidate = submitted_by_id[current["candidate_id"]]
        candidate["source_refs"] = current.get("source_refs", [])
        candidate["candidate_status"] = 'ACTIVE'
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
        'PREVIEW_READY',
        payload.expected_revision,
        preview,
        user.id,
        now(),
        review_note=payload.review_note,
    )
    if not updated:
        raise HTTPException(
            status_code=409, detail={"code": 'REVISION_CONFLICT'}
        )
    await audit(
        user.id,
        'requirement_import_reviewed',
        'RequirementImport',
        job_id,
        job["project_id"],
        {"candidate_count": len(preview), "review_note": payload.review_note},
    )
    return updated


async def merge_requirement_import_candidates(job_id, payload, user):
    
    job = await get_project_entity(
        'import_jobs', job_id, user, 'requirement_document.review_extraction'
    )
    if job.get("status") != 'PREVIEW_READY':
        raise HTTPException(
            status_code=409, detail={"code": 'IMPORT_PREVIEW_NOT_EDITABLE'}
        )
    candidate_ids = list(dict.fromkeys(payload.candidate_ids))
    if len(candidate_ids) != len(payload.candidate_ids):
        raise HTTPException(
            status_code=422, detail={"code": 'DUPLICATE_CANDIDATE_ID'}
        )
    preview = prepare_requirement_candidates(job_id, job.get("preview", []))
    by_id = {item["candidate_id"]: item for item in preview}
    if not set(candidate_ids) <= set(by_id):
        raise HTTPException(
            status_code=404, detail={"code": 'CANDIDATE_NOT_FOUND'}
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
    merged_id = new_id('RCAND')
    merged.update(
        {
            "candidate_id": merged_id,
            "candidate_status": 'ACTIVE',
            "candidate_revision": 1,
            "candidate_relation": 'merged',
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
        "_id": new_id('RCOP'),
        "type": 'MERGE',
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
        'PREVIEW_READY',
        payload.expected_revision,
        next_preview,
        user.id,
        now(),
        push_field="candidate_lineage",
        push_value=event,
    )
    if not updated:
        raise HTTPException(
            status_code=409, detail={"code": 'REVISION_CONFLICT'}
        )
    await audit(
        user.id,
        'requirement_candidates_merged',
        'RequirementImport',
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
    
    job = await get_project_entity(
        'import_jobs', job_id, user, 'requirement_document.review_extraction'
    )
    if job.get("status") != 'PREVIEW_READY':
        raise HTTPException(
            status_code=409, detail={"code": 'IMPORT_PREVIEW_NOT_EDITABLE'}
        )
    preview = prepare_requirement_candidates(job_id, job.get("preview", []))
    parent = next((item for item in preview if item["candidate_id"] == candidate_id), None)
    if not parent:
        raise HTTPException(
            status_code=404, detail={"code": 'CANDIDATE_NOT_FOUND'}
        )
    if len(preview) - 1 + len(payload.drafts) > 500:
        raise HTTPException(
            status_code=422, detail={"code": 'CANDIDATE_LIMIT_EXCEEDED'}
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
                "candidate_id": new_id('RCAND'),
                "candidate_status": 'ACTIVE',
                "candidate_revision": 1,
                "candidate_relation": f"{'split'}-{index + 1}",
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
        "_id": new_id('RCOP'),
        "type": 'SPLIT',
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
        'PREVIEW_READY',
        payload.expected_revision,
        next_preview,
        user.id,
        now(),
        push_field="candidate_lineage",
        push_value=event,
    )
    if not updated:
        raise HTTPException(
            status_code=409, detail={"code": 'REVISION_CONFLICT'}
        )
    await audit(
        user.id,
        'requirement_candidate_split',
        'RequirementImport',
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
    
    job = await get_project_entity(
        'import_jobs', job_id, user, 'requirement_document.review_extraction'
    )
    if job.get("status") != 'PREVIEW_READY':
        raise HTTPException(
            status_code=409, detail={"code": 'IMPORT_PREVIEW_NOT_EDITABLE'}
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
            status_code=404, detail={"code": 'CANDIDATE_NOT_FOUND'}
        )
    rejected = {
        **candidate,
        "candidate_status": 'REJECTED',
        "candidate_revision": int(candidate.get("candidate_revision", 1)) + 1,
        "rejection_reason": payload.reason,
        "rejected_by": user.id,
        "rejected_at": now(),
    }
    next_preview = [item for item in preview if item["candidate_id"] != candidate_id]
    updated = await requirement_import_repository.update_preview(
        job_id,
        job["project_id"],
        'PREVIEW_READY',
        payload.expected_revision,
        next_preview,
        user.id,
        now(),
        push_field="rejected_candidates",
        push_value=rejected,
    )
    if not updated:
        raise HTTPException(
            status_code=409, detail={"code": 'REVISION_CONFLICT'}
        )
    await audit(
        user.id,
        'requirement_candidate_rejected',
        'RequirementImport',
        job_id,
        job["project_id"],
        {"candidate_id": candidate_id, "reason": payload.reason},
    )
    return updated


async def confirm_requirement_import_job(job_id, payload, user):
    
    job = await get_project_entity(
        'import_jobs', job_id, user, 'requirement_document.confirm_extraction'
    )
    await get_project(job["project_id"], user, 'requirement.create')
    if job["status"] == 'CONFIRMED':
        return {"job": job, "requirements": None}
    indexes = payload.selected_indexes or list(range(len(job["preview"])))
    indexes = list(dict.fromkeys(indexes))
    for index in indexes:
        if index < 0 or index >= len(job["preview"]):
            raise HTTPException(
                status_code=422,
                detail={"code": 'INVALID_PREVIEW_INDEX'},
            )
    claimed = await requirement_import_repository.claim_confirmation(
        job_id,
        job["project_id"],
        'PREVIEW_READY',
        'CONFIRMING',
        user.id,
        now(),
        payload.expected_revision,
    )
    if not claimed:
        current = await requirement_import_repository.find(job_id, job["project_id"])
        if current and current.get("status") == 'CONFIRMED':
            return {"job": current, "requirements": None}
        raise HTTPException(
            status_code=409,
            detail={"code": 'IMPORT_CONFIRM_IN_PROGRESS'},
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
                    origin='import',
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
            'CONFIRMING',
            'PREVIEW_READY',
            now(),
        )
        await audit(
            user.id,
            'requirement_import_confirmation_failed',
            'RequirementImport',
            job_id,
            job["project_id"],
        )
        raise
    rejected_indexes = [index for index in range(len(job["preview"])) if index not in indexes]
    await requirement_import_repository.confirm(
        job_id,
        job["project_id"],
        'CONFIRMING',
        'CONFIRMED',
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
            'CONFIRMED',
            now(),
        )
    await audit(
        user.id,
        'requirement_import_confirmed',
        'RequirementImport',
        job_id,
        job["project_id"],
        {
            "created_requirement_ids": [item["_id"] for item in created],
            "selected_indexes": indexes,
            "rejected_indexes": rejected_indexes,
        },
    )
    return {"job": None, "requirements": created}
