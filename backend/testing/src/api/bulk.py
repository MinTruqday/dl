from fastapi import APIRouter, Depends, HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.api.changes import apply_proposal, create_maintenance_proposals
from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, new_id, now
from src.core.database import database
from src.domain.schemas import (
    BulkArchiveInput,
    BulkProposalApproveInput,
    BulkProposalGenerateInput,
    BulkReviewRequiredInput,
    BulkSuiteInput,
    BulkTagInput,
    ProposalAction,
)


router = APIRouter(prefix="/kiem-thu", tags=["Tác vụ kiểm thử hàng loạt"])


async def finish_operation(
    project_id,
    operation_type,
    succeeded,
    failed,
    user,
    *,
    idempotency_key=None,
    preview=False,
    results=None,
    details=None,
):
    if idempotency_key:
        existing = await database.value.bulk_operations.find_one(
            {"project_id": project_id, "idempotency_key": idempotency_key}
        )
        if existing:
            return envelope(existing["response"])
    operation = {
        "_id": new_id("OP"),
        "operation_id": new_id("OPR"),
        "project_id": project_id,
        "operation_type": operation_type,
        "succeeded": succeeded,
        "failed": failed,
        "created_by": user.id,
        "created_at": now(),
        "idempotency_key": idempotency_key,
        "preview": preview,
    }
    response = {
        "operation_id": operation["operation_id"],
        "operation_type": operation_type,
        "status": "PREVIEW" if preview else "COMPLETED",
        "preview": preview,
        "succeeded": succeeded,
        "failed": failed,
        "results": results or [],
        "details": details or {},
    }
    operation["response"] = response
    try:
        await database.value.bulk_operations.insert_one(operation)
    except DuplicateKeyError:
        if idempotency_key:
            existing = await database.value.bulk_operations.find_one(
                {"project_id": project_id, "idempotency_key": idempotency_key}
            )
            if existing:
                return envelope(existing["response"])
        raise
    await audit(
        user.id,
        "bulk_operation_completed",
        "BulkOperation",
        operation["_id"],
        project_id,
        {
            "operation_type": operation_type,
            "succeeded": len(succeeded),
            "failed": len(failed),
            "preview": preview,
        },
    )
    return envelope(response)


def operation_key(payload):
    return payload.idempotency_key or new_id("LEGACY")


async def replay_operation(project_id, idempotency_key):
    if not idempotency_key:
        return None
    existing = await database.value.bulk_operations.find_one(
        {"project_id": project_id, "idempotency_key": idempotency_key}
    )
    return envelope(existing["response"]) if existing else None


def item_result(item_id, status, code=None, **details):
    result = {"id": item_id, "status": status}
    if code:
        result["code"] = code
    result.update(details)
    return result


async def fresh_proposal(proposal):
    proposal_type = proposal.get("proposal_type")
    if proposal_type not in {"UPDATE_TEST_CASE", "MARK_OBSOLETE"}:
        return True
    target = await database.value.test_cases.find_one(
        {"_id": proposal.get("target_artifact_id"), "project_id": proposal["project_id"]},
        {"current_version_id": 1},
    )
    return bool(target and target.get("current_version_id") == proposal.get("base_version_id"))


@router.post("/du-an/{project_id}/hang-loat/nhan")
async def bulk_tags(
    project_id: str,
    payload: BulkTagInput,
    user: CurrentUser = Depends(get_current_user),
):
    permission = "requirement.update" if payload.artifact_type == "requirement" else "testcase.bulk.update"
    await get_project(project_id, user, permission)
    idempotency_key = operation_key(payload)
    replay = await replay_operation(project_id, idempotency_key)
    if replay:
        return replay
    add_tags = {value.strip() for value in payload.add_tags if value.strip()}
    remove_tags = {value.strip() for value in payload.remove_tags if value.strip()}
    if not add_tags and not remove_tags:
        raise HTTPException(status_code=422, detail={"code": "EMPTY_BULK_OPERATION"})
    if any(len(value) > 100 for value in add_tags | remove_tags):
        raise HTTPException(status_code=422, detail={"code": "INVALID_TAG"})
    collection = "requirements" if payload.artifact_type == "requirement" else "test_cases"
    succeeded = []
    failed = []
    results = []
    for artifact_id in dict.fromkeys(payload.ids):
        artifact = await database.value[collection].find_one(
            {"_id": artifact_id, "project_id": project_id}
        )
        if not artifact:
            failed.append({"id": artifact_id, "code": "ENTITY_NOT_FOUND"})
            results.append(item_result(artifact_id, "FAILED", "ENTITY_NOT_FOUND"))
            continue
        tags = (set(artifact.get("tags", [])) | add_tags) - remove_tags
        if payload.preview:
            succeeded.append(artifact_id)
            results.append(
                item_result(
                    artifact_id,
                    "PREVIEW",
                    before_tags=sorted(artifact.get("tags", [])),
                    after_tags=sorted(tags),
                )
            )
            continue
        result = await database.value[collection].update_one(
            {"_id": artifact_id, "project_id": project_id},
            {"$set": {"tags": sorted(tags), "updated_at": now()}},
        )
        if result.matched_count:
            succeeded.append(artifact_id)
            results.append(item_result(artifact_id, "SUCCEEDED", tags=sorted(tags)))
        else:
            failed.append({"id": artifact_id, "code": "REVISION_CONFLICT"})
            results.append(item_result(artifact_id, "FAILED", "REVISION_CONFLICT"))
    return await finish_operation(
        project_id,
        "BULK_TAGS",
        succeeded,
        failed,
        user,
        idempotency_key=idempotency_key,
        preview=payload.preview,
        results=results,
        details={"artifact_type": payload.artifact_type, "add_tags": sorted(add_tags), "remove_tags": sorted(remove_tags)},
    )


@router.post("/du-an/{project_id}/hang-loat/ca-kiem-thu/them-vao-bo-kiem-thu")
async def bulk_add_to_suite(
    project_id: str,
    payload: BulkSuiteInput,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "testcase.bulk.update")
    idempotency_key = operation_key(payload)
    replay = await replay_operation(project_id, idempotency_key)
    if replay:
        return replay
    suite = await database.value.test_suites.find_one(
        {"_id": payload.suite_id, "project_id": project_id}
    )
    if not suite:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    if suite.get("revision", 1) != payload.expected_revision:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    succeeded = []
    failed = []
    results = []
    version_ids = set(suite.get("test_case_version_ids", []))
    for test_case_id in dict.fromkeys(payload.test_case_ids):
        test_case = await database.value.test_cases.find_one(
            {"_id": test_case_id, "project_id": project_id, "status": {"$ne": "OBSOLETE"}}
        )
        if not test_case or not test_case.get("current_version_id"):
            failed.append({"id": test_case_id, "code": "ENTITY_NOT_FOUND"})
            results.append(item_result(test_case_id, "FAILED", "ENTITY_NOT_FOUND"))
            continue
        version_ids.add(test_case["current_version_id"])
        succeeded.append(test_case_id)
        results.append(item_result(test_case_id, "PREVIEW" if payload.preview else "SUCCEEDED", version_id=test_case["current_version_id"]))
    if payload.preview:
        return await finish_operation(
            project_id, "BULK_ADD_TO_SUITE", succeeded, failed, user,
            idempotency_key=idempotency_key, preview=True, results=results,
            details={"suite_id": payload.suite_id, "resulting_version_ids": sorted(version_ids)},
        )
    updated = await database.value.test_suites.find_one_and_update(
        {"_id": payload.suite_id, "project_id": project_id, "revision": payload.expected_revision},
        {
            "$set": {"test_case_version_ids": sorted(version_ids), "updated_at": now()},
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    return await finish_operation(
        project_id, "BULK_ADD_TO_SUITE", succeeded, failed, user,
        idempotency_key=idempotency_key, results=results,
        details={"suite_id": payload.suite_id, "resulting_version_ids": sorted(version_ids)},
    )


@router.post("/du-an/{project_id}/hang-loat/ca-kiem-thu/danh-dau-can-ra-soat")
async def bulk_mark_review_required(
    project_id: str,
    payload: BulkReviewRequiredInput,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "testcase.bulk.update")
    idempotency_key = operation_key(payload)
    replay = await replay_operation(project_id, idempotency_key)
    if replay:
        return replay
    succeeded = []
    failed = []
    results = []
    for test_case_id in dict.fromkeys(payload.test_case_ids):
        test_case = await database.value.test_cases.find_one(
            {"_id": test_case_id, "project_id": project_id, "status": {"$ne": "OBSOLETE"}},
            {"_id": 1},
        )
        result = None if payload.preview else await database.value.test_cases.update_one(
            {"_id": test_case_id, "project_id": project_id, "status": {"$ne": "OBSOLETE"}},
            {
                "$set": {
                    "status": "NEEDS_UPDATE",
                    "review_required_reason": payload.reason,
                    "review_required_by": user.id,
                    "updated_at": now(),
                }
            },
        )
        if (payload.preview and test_case) or (result and result.matched_count):
            succeeded.append(test_case_id)
            results.append(item_result(test_case_id, "PREVIEW" if payload.preview else "SUCCEEDED"))
        else:
            failed.append({"id": test_case_id, "code": "ENTITY_NOT_FOUND"})
            results.append(item_result(test_case_id, "FAILED", "ENTITY_NOT_FOUND"))
    return await finish_operation(
        project_id, "BULK_MARK_REVIEW_REQUIRED", succeeded, failed, user,
        idempotency_key=idempotency_key, preview=payload.preview, results=results,
        details={"reason": payload.reason},
    )


@router.post("/du-an/{project_id}/hang-loat/luu-tru")
async def bulk_archive(
    project_id: str,
    payload: BulkArchiveInput,
    user: CurrentUser = Depends(get_current_user),
):
    permission = "requirement.archive" if payload.artifact_type == "requirement" else "testcase.bulk.archive"
    await get_project(project_id, user, permission)
    idempotency_key = operation_key(payload)
    replay = await replay_operation(project_id, idempotency_key)
    if replay:
        return replay
    collection = "requirements" if payload.artifact_type == "requirement" else "test_cases"
    succeeded = []
    failed = []
    results = []
    for artifact_id in dict.fromkeys(payload.ids):
        artifact = await database.value[collection].find_one(
            {"_id": artifact_id, "project_id": project_id}
        )
        if not artifact:
            failed.append({"id": artifact_id, "code": "ENTITY_NOT_FOUND"})
            results.append(item_result(artifact_id, "FAILED", "ENTITY_NOT_FOUND"))
            continue
        if artifact.get("status") == "OBSOLETE":
            failed.append({"id": artifact_id, "code": "ALREADY_ARCHIVED"})
            results.append(item_result(artifact_id, "FAILED", "ALREADY_ARCHIVED"))
            continue
        if payload.artifact_type == "test_case":
            active_run = await database.value.test_runs.find_one(
                {
                    "project_id": project_id,
                    "status": {"$in": ["DRAFT", "READY", "IN_PROGRESS"]},
                    "test_case_version_ids": artifact.get("current_version_id"),
                },
                {"_id": 1},
            )
            if active_run:
                failed.append({"id": artifact_id, "code": "ACTIVE_RUN_LINK"})
                results.append(item_result(artifact_id, "FAILED", "ACTIVE_RUN_LINK"))
                continue
        if payload.preview:
            succeeded.append(artifact_id)
            results.append(item_result(artifact_id, "PREVIEW", current_status=artifact.get("status", "ACTIVE"), target_status="OBSOLETE"))
            continue
        result = await database.value[collection].update_one(
            {"_id": artifact_id, "project_id": project_id, "current_version_id": artifact.get("current_version_id")},
            {
                "$set": {
                    "status": "OBSOLETE",
                    "obsolete_reason": payload.reason,
                    "obsolete_by": user.id,
                    "obsolete_at": now(),
                    "updated_at": now(),
                }
            },
        )
        if result.matched_count:
            succeeded.append(artifact_id)
            results.append(item_result(artifact_id, "SUCCEEDED", target_status="OBSOLETE"))
        else:
            failed.append({"id": artifact_id, "code": "REVISION_CONFLICT"})
            results.append(item_result(artifact_id, "FAILED", "REVISION_CONFLICT"))
    return await finish_operation(
        project_id, "BULK_ARCHIVE", succeeded, failed, user,
        idempotency_key=idempotency_key, preview=payload.preview, results=results,
        details={"artifact_type": payload.artifact_type, "reason": payload.reason},
    )


@router.post("/du-an/{project_id}/hang-loat/de-xuat-anh-huong")
async def bulk_generate_proposals(
    project_id: str,
    payload: BulkProposalGenerateInput,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "proposal.bulk.generate")
    idempotency_key = operation_key(payload)
    replay = await replay_operation(project_id, idempotency_key)
    if replay:
        return replay
    succeeded = []
    failed = []
    results = []
    for analysis_id in dict.fromkeys(payload.impact_analysis_ids):
        analysis = await database.value.impact_analyses.find_one(
            {"_id": analysis_id, "project_id": project_id}
        )
        if not analysis:
            failed.append({"id": analysis_id, "code": "ENTITY_NOT_FOUND"})
            results.append(item_result(analysis_id, "FAILED", "ENTITY_NOT_FOUND"))
            continue
        if payload.preview:
            succeeded.append(analysis_id)
            results.append(item_result(analysis_id, "PREVIEW", analysis_status=analysis.get("status"), proposal_count=await database.value.maintenance_proposals.count_documents({"impact_analysis_id": analysis_id})))
            continue
        try:
            await create_maintenance_proposals(analysis_id, user)
            succeeded.append(analysis_id)
            results.append(item_result(analysis_id, "SUCCEEDED"))
        except HTTPException as error:
            detail = error.detail if isinstance(error.detail, dict) else {}
            failed.append({"id": analysis_id, "code": detail.get("code", "REQUEST_FAILED")})
            results.append(item_result(analysis_id, "FAILED", detail.get("code", "REQUEST_FAILED")))
    return await finish_operation(
        project_id, "BULK_GENERATE_PROPOSALS", succeeded, failed, user,
        idempotency_key=idempotency_key, preview=payload.preview, results=results,
    )


@router.post("/du-an/{project_id}/hang-loat/phe-duyet-de-xuat")
async def bulk_approve_proposals(
    project_id: str,
    payload: BulkProposalApproveInput,
    user: CurrentUser = Depends(get_current_user),
):
    project = await get_project(project_id, user, "proposal.bulk.approve")
    idempotency_key = operation_key(payload)
    replay = await replay_operation(project_id, idempotency_key)
    if replay:
        return replay
    threshold = float(project.get("settings", {}).get("impact_confidence_threshold", 0.75))
    succeeded = []
    failed = []
    results = []
    for proposal_id in dict.fromkeys(payload.proposal_ids):
        proposal = await database.value.maintenance_proposals.find_one(
            {"_id": proposal_id, "project_id": project_id}
        )
        if not proposal:
            failed.append({"id": proposal_id, "code": "ENTITY_NOT_FOUND"})
            results.append(item_result(proposal_id, "FAILED", "ENTITY_NOT_FOUND"))
            continue
        if proposal.get("status") != "PENDING":
            failed.append({"id": proposal_id, "code": "INVALID_STATE_TRANSITION"})
            results.append(item_result(proposal_id, "FAILED", "INVALID_STATE_TRANSITION"))
            continue
        if not proposal.get("last_reviewed_by"):
            failed.append({"id": proposal_id, "code": "PROPOSAL_REVIEW_REQUIRED"})
            results.append(item_result(proposal_id, "FAILED", "PROPOSAL_REVIEW_REQUIRED", target_artifact_id=proposal.get("target_artifact_id")))
            continue
        if float(proposal.get("confidence", 0)) < threshold:
            failed.append({"id": proposal_id, "code": "POLICY_THRESHOLD_NOT_MET"})
            results.append(item_result(proposal_id, "FAILED", "POLICY_THRESHOLD_NOT_MET", confidence=proposal.get("confidence", 0), threshold=threshold))
            continue
        if not await fresh_proposal(proposal):
            failed.append({"id": proposal_id, "code": "STALE_PROPOSAL"})
            results.append(item_result(proposal_id, "FAILED", "STALE_PROPOSAL", target_artifact_id=proposal.get("target_artifact_id"), base_version_id=proposal.get("base_version_id")))
            continue
        if payload.preview:
            succeeded.append(proposal_id)
            results.append(item_result(proposal_id, "PREVIEW", target_artifact_id=proposal.get("target_artifact_id"), base_version_id=proposal.get("base_version_id")))
            continue
        try:
            await apply_proposal(
                proposal_id,
                ProposalAction(
                    expected_revision=proposal["revision"],
                    review_note=payload.review_note,
                ),
                user,
                "ACCEPTED",
            )
            succeeded.append(proposal_id)
            results.append(item_result(proposal_id, "SUCCEEDED", target_artifact_id=proposal.get("target_artifact_id")))
        except HTTPException as error:
            detail = error.detail if isinstance(error.detail, dict) else {}
            failed.append({"id": proposal_id, "code": detail.get("code", "REQUEST_FAILED")})
            results.append(item_result(proposal_id, "FAILED", detail.get("code", "REQUEST_FAILED"), target_artifact_id=proposal.get("target_artifact_id")))
    return await finish_operation(
        project_id, "BULK_APPROVE_PROPOSALS", succeeded, failed, user,
        idempotency_key=idempotency_key, preview=payload.preview, results=results,
        details={"review_note": payload.review_note, "confidence_threshold": threshold},
    )
