from fastapi import APIRouter, Depends, HTTPException
from pymongo import ReturnDocument

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


router = APIRouter(prefix="/api/qa", tags=["QA Bulk Operations"])


async def finish_operation(project_id, operation_type, succeeded, failed, user):
    operation = {
        "_id": new_id("OP"),
        "operation_id": new_id("OPR"),
        "project_id": project_id,
        "operation_type": operation_type,
        "succeeded": succeeded,
        "failed": failed,
        "created_by": user.id,
        "created_at": now(),
    }
    await database.value.bulk_operations.insert_one(operation)
    await audit(
        user.id,
        "bulk_operation_completed",
        "BulkOperation",
        operation["_id"],
        project_id,
        {"operation_type": operation_type, "succeeded": len(succeeded), "failed": len(failed)},
    )
    return envelope(
        {
            "operation_id": operation["operation_id"],
            "succeeded": succeeded,
            "failed": failed,
        }
    )


@router.post("/projects/{project_id}/bulk/tags")
async def bulk_tags(
    project_id: str,
    payload: BulkTagInput,
    user: CurrentUser = Depends(get_current_user),
):
    permission = "requirement.update" if payload.artifact_type == "requirement" else "testcase.update"
    await get_project(project_id, user, permission)
    add_tags = {value.strip() for value in payload.add_tags if value.strip()}
    remove_tags = {value.strip() for value in payload.remove_tags if value.strip()}
    if not add_tags and not remove_tags:
        raise HTTPException(status_code=422, detail={"code": "EMPTY_BULK_OPERATION"})
    if any(len(value) > 100 for value in add_tags | remove_tags):
        raise HTTPException(status_code=422, detail={"code": "INVALID_TAG"})
    collection = "requirements" if payload.artifact_type == "requirement" else "test_cases"
    succeeded = []
    failed = []
    for artifact_id in dict.fromkeys(payload.ids):
        artifact = await database.value[collection].find_one(
            {"_id": artifact_id, "project_id": project_id}
        )
        if not artifact:
            failed.append({"id": artifact_id, "code": "ENTITY_NOT_FOUND"})
            continue
        tags = (set(artifact.get("tags", [])) | add_tags) - remove_tags
        result = await database.value[collection].update_one(
            {"_id": artifact_id, "project_id": project_id},
            {"$set": {"tags": sorted(tags), "updated_at": now()}},
        )
        if result.matched_count:
            succeeded.append(artifact_id)
        else:
            failed.append({"id": artifact_id, "code": "REVISION_CONFLICT"})
    return await finish_operation(project_id, "BULK_TAGS", succeeded, failed, user)


@router.post("/projects/{project_id}/bulk/test-cases/add-to-suite")
async def bulk_add_to_suite(
    project_id: str,
    payload: BulkSuiteInput,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "testsuite.update")
    suite = await database.value.test_suites.find_one(
        {"_id": payload.suite_id, "project_id": project_id}
    )
    if not suite:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    if suite.get("revision", 1) != payload.expected_revision:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    succeeded = []
    failed = []
    version_ids = set(suite.get("test_case_version_ids", []))
    for test_case_id in dict.fromkeys(payload.test_case_ids):
        test_case = await database.value.test_cases.find_one(
            {"_id": test_case_id, "project_id": project_id, "status": {"$ne": "OBSOLETE"}}
        )
        if not test_case or not test_case.get("current_version_id"):
            failed.append({"id": test_case_id, "code": "ENTITY_NOT_FOUND"})
            continue
        version_ids.add(test_case["current_version_id"])
        succeeded.append(test_case_id)
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
    return await finish_operation(project_id, "BULK_ADD_TO_SUITE", succeeded, failed, user)


@router.post("/projects/{project_id}/bulk/test-cases/mark-review-required")
async def bulk_mark_review_required(
    project_id: str,
    payload: BulkReviewRequiredInput,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "testcase.update")
    succeeded = []
    failed = []
    for test_case_id in dict.fromkeys(payload.test_case_ids):
        result = await database.value.test_cases.update_one(
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
        if result.matched_count:
            succeeded.append(test_case_id)
        else:
            failed.append({"id": test_case_id, "code": "ENTITY_NOT_FOUND"})
    return await finish_operation(project_id, "BULK_MARK_REVIEW_REQUIRED", succeeded, failed, user)


@router.post("/projects/{project_id}/bulk/archive")
async def bulk_archive(
    project_id: str,
    payload: BulkArchiveInput,
    user: CurrentUser = Depends(get_current_user),
):
    permission = "requirement.archive" if payload.artifact_type == "requirement" else "testcase.archive"
    await get_project(project_id, user, permission)
    collection = "requirements" if payload.artifact_type == "requirement" else "test_cases"
    succeeded = []
    failed = []
    for artifact_id in dict.fromkeys(payload.ids):
        artifact = await database.value[collection].find_one(
            {"_id": artifact_id, "project_id": project_id}
        )
        if not artifact:
            failed.append({"id": artifact_id, "code": "ENTITY_NOT_FOUND"})
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
        else:
            failed.append({"id": artifact_id, "code": "REVISION_CONFLICT"})
    return await finish_operation(project_id, "BULK_ARCHIVE", succeeded, failed, user)


@router.post("/projects/{project_id}/bulk/impact-proposals")
async def bulk_generate_proposals(
    project_id: str,
    payload: BulkProposalGenerateInput,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "ai.create_proposal")
    succeeded = []
    failed = []
    for analysis_id in dict.fromkeys(payload.impact_analysis_ids):
        analysis = await database.value.impact_analyses.find_one(
            {"_id": analysis_id, "project_id": project_id}
        )
        if not analysis:
            failed.append({"id": analysis_id, "code": "ENTITY_NOT_FOUND"})
            continue
        try:
            await create_maintenance_proposals(analysis_id, user)
            succeeded.append(analysis_id)
        except HTTPException as error:
            detail = error.detail if isinstance(error.detail, dict) else {}
            failed.append({"id": analysis_id, "code": detail.get("code", "REQUEST_FAILED")})
    return await finish_operation(project_id, "BULK_GENERATE_PROPOSALS", succeeded, failed, user)


@router.post("/projects/{project_id}/bulk/approve-proposals")
async def bulk_approve_proposals(
    project_id: str,
    payload: BulkProposalApproveInput,
    user: CurrentUser = Depends(get_current_user),
):
    project = await get_project(project_id, user, "proposal.approve")
    threshold = float(project.get("settings", {}).get("impact_confidence_threshold", 0.75))
    succeeded = []
    failed = []
    for proposal_id in dict.fromkeys(payload.proposal_ids):
        proposal = await database.value.maintenance_proposals.find_one(
            {"_id": proposal_id, "project_id": project_id}
        )
        if not proposal:
            failed.append({"id": proposal_id, "code": "ENTITY_NOT_FOUND"})
            continue
        if proposal.get("status") != "PENDING":
            failed.append({"id": proposal_id, "code": "INVALID_STATE_TRANSITION"})
            continue
        if float(proposal.get("confidence", 0)) < threshold:
            failed.append({"id": proposal_id, "code": "POLICY_THRESHOLD_NOT_MET"})
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
        except HTTPException as error:
            detail = error.detail if isinstance(error.detail, dict) else {}
            failed.append({"id": proposal_id, "code": detail.get("code", "REQUEST_FAILED")})
    return await finish_operation(project_id, "BULK_APPROVE_PROPOSALS", succeeded, failed, user)
