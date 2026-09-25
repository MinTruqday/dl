from fastapi import HTTPException

from src.core.auth import CurrentUser
from src.core.common import audit, get_project_entity, now
from src.repositories.requirement import requirement_repository
from src.services.domain_policy import domain_policy
from src.services.linters import requirement_findings
from src.services.requirement_indexing import index_requirement_version

LIFECYCLE_POLICY = domain_policy("requirement_lifecycle")


async def submit_requirement_for_review(
    project_id: str,
    requirement_id: str,
    expected_revision: int,
    review_note: str,
    user: CurrentUser,
):
    requirement = await get_project_entity(
        LIFECYCLE_POLICY["requirement_collection"],
        requirement_id,
        user,
        LIFECYCLE_POLICY["submit_permission"],
    )
    if requirement["project_id"] != project_id:
        raise HTTPException(
            status_code=422,
            detail={"code": LIFECYCLE_POLICY["project_mismatch_code"]},
        )
    version = await requirement_repository.find_version(
        requirement["current_version_id"], project_id
    )
    if version["status"] == LIFECYCLE_POLICY["review_status"]:
        return version
    if version["status"] != LIFECYCLE_POLICY["draft_status"]:
        raise HTTPException(
            status_code=409,
            detail={"code": LIFECYCLE_POLICY["invalid_transition_code"]},
        )
    if version["revision"] != expected_revision:
        raise HTTPException(
            status_code=409,
            detail={
                "code": LIFECYCLE_POLICY["revision_conflict_code"],
                "current_revision": version["revision"],
            },
        )
    acceptance_criteria = await requirement_repository.list_acceptance_criteria(
        version["_id"], LIFECYCLE_POLICY["acceptance_criteria_limit"]
    )
    findings = requirement_findings(version, acceptance_criteria)
    project = await requirement_repository.find_project_settings(project_id)
    lint_blocking = (project.get("settings") or {}).get(
        LIFECYCLE_POLICY["lint_setting"], LIFECYCLE_POLICY["lint_setting_default"]
    )
    if lint_blocking and any(
        item["severity"] == LIFECYCLE_POLICY["lint_blocking_severity"] for item in findings
    ):
        raise HTTPException(
            status_code=409,
            detail={"code": LIFECYCLE_POLICY["lint_blocked_code"], "findings": findings},
        )
    timestamp = now()
    transitioned = await requirement_repository.transition_version(
        version["_id"],
        project_id,
        expected_revision,
        LIFECYCLE_POLICY["draft_status"],
        LIFECYCLE_POLICY["review_status"],
        {
            "review_note": review_note,
            "review_submitted_by": user.id,
            "review_submitted_at": timestamp,
            "updated_at": timestamp,
        },
    )
    if not transitioned:
        raise HTTPException(
            status_code=409,
            detail={"code": LIFECYCLE_POLICY["revision_conflict_code"]},
        )
    await requirement_repository.set_requirement_status(
        requirement_id, project_id, LIFECYCLE_POLICY["review_status"], timestamp
    )
    version = await requirement_repository.find_version(version["_id"], project_id)
    await audit(
        user.id,
        LIFECYCLE_POLICY["review_submitted_event"],
        LIFECYCLE_POLICY["version_entity"],
        version["_id"],
        project_id,
        {"review_note": review_note},
    )
    return version


async def return_requirement_for_changes(
    project_id: str,
    requirement_id: str,
    expected_revision: int,
    review_note: str,
    user: CurrentUser,
):
    requirement = await get_project_entity(
        LIFECYCLE_POLICY["requirement_collection"],
        requirement_id,
        user,
        LIFECYCLE_POLICY["review_permission"],
    )
    if requirement["project_id"] != project_id:
        raise HTTPException(
            status_code=422,
            detail={"code": LIFECYCLE_POLICY["project_mismatch_code"]},
        )
    version = await requirement_repository.find_version(
        requirement["current_version_id"], project_id
    )
    if version["status"] != LIFECYCLE_POLICY["review_status"]:
        raise HTTPException(
            status_code=409,
            detail={"code": LIFECYCLE_POLICY["invalid_transition_code"]},
        )
    if version["revision"] != expected_revision:
        raise HTTPException(
            status_code=409,
            detail={
                "code": LIFECYCLE_POLICY["revision_conflict_code"],
                "current_revision": version["revision"],
            },
        )
    timestamp = now()
    transitioned = await requirement_repository.transition_version(
        version["_id"],
        project_id,
        expected_revision,
        LIFECYCLE_POLICY["review_status"],
        LIFECYCLE_POLICY["draft_status"],
        {
            "review_note": review_note,
            "changes_requested_by": user.id,
            "changes_requested_at": timestamp,
            "updated_at": timestamp,
        },
    )
    if not transitioned:
        raise HTTPException(
            status_code=409,
            detail={"code": LIFECYCLE_POLICY["revision_conflict_code"]},
        )
    await requirement_repository.set_requirement_status(
        requirement_id, project_id, LIFECYCLE_POLICY["draft_status"], timestamp
    )
    version = await requirement_repository.find_version(version["_id"], project_id)
    await audit(
        user.id,
        LIFECYCLE_POLICY["changes_requested_event"],
        LIFECYCLE_POLICY["version_entity"],
        version["_id"],
        project_id,
        {"review_note": review_note},
    )
    return version


async def baseline_requirement(
    version_id: str,
    expected_revision: int,
    review_note: str,
    user: CurrentUser,
):
    version = await get_project_entity(
        LIFECYCLE_POLICY["version_collection"],
        version_id,
        user,
        LIFECYCLE_POLICY["approve_permission"],
    )
    if version["status"] == LIFECYCLE_POLICY["baselined_status"]:
        return version, True
    if version["status"] != LIFECYCLE_POLICY["review_status"]:
        raise HTTPException(
            status_code=409,
            detail={"code": LIFECYCLE_POLICY["invalid_transition_code"]},
        )
    if version["revision"] != expected_revision:
        raise HTTPException(
            status_code=409,
            detail={
                "code": LIFECYCLE_POLICY["revision_conflict_code"],
                "current_revision": version["revision"],
            },
        )
    acceptance_criteria = await requirement_repository.list_acceptance_criteria(
        version["_id"], LIFECYCLE_POLICY["acceptance_criteria_limit"]
    )
    findings = requirement_findings(version, acceptance_criteria)
    project = await requirement_repository.find_project_settings(version["project_id"])
    lint_blocking = (project.get("settings") or {}).get(
        LIFECYCLE_POLICY["lint_setting"], LIFECYCLE_POLICY["lint_setting_default"]
    )
    if lint_blocking and any(
        item["severity"] == LIFECYCLE_POLICY["lint_blocking_severity"] for item in findings
    ):
        raise HTTPException(
            status_code=409,
            detail={"code": LIFECYCLE_POLICY["lint_blocked_code"], "findings": findings},
        )
    timestamp = now()
    version = await requirement_repository.baseline_version(
        version_id,
        version["project_id"],
        expected_revision,
        LIFECYCLE_POLICY["review_status"],
        {
            "status": LIFECYCLE_POLICY["baselined_status"],
            "review_note": review_note,
            "baselined_at": timestamp,
            "baselined_by": user.id,
            "updated_at": timestamp,
        },
    )
    if not version:
        current = await requirement_repository.find_version(version_id)
        if current and current.get("status") == LIFECYCLE_POLICY["baselined_status"]:
            return current, True
        raise HTTPException(
            status_code=409,
            detail={"code": LIFECYCLE_POLICY["revision_conflict_code"]},
        )
    await requirement_repository.set_current_baseline(
        version["requirement_id"],
        version_id,
        LIFECYCLE_POLICY["baselined_status"],
        timestamp,
    )
    await requirement_repository.approve_acceptance_criteria(
        version_id,
        LIFECYCLE_POLICY["draft_criterion_status"],
        LIFECYCLE_POLICY["approved_criterion_status"],
        timestamp,
        user.id,
    )
    indexed = await index_requirement_version(version)
    version = await requirement_repository.find_version(version_id)
    await audit(
        user.id,
        LIFECYCLE_POLICY["baselined_event"],
        LIFECYCLE_POLICY["version_entity"],
        version_id,
        version["project_id"],
    )
    return version, indexed


async def make_requirement_obsolete(
    requirement_id: str,
    expected_current_version_id: str,
    reason: str,
    user: CurrentUser,
):
    requirement = await get_project_entity(
        LIFECYCLE_POLICY["requirement_collection"],
        requirement_id,
        user,
        LIFECYCLE_POLICY["archive_permission"],
    )
    if requirement.get("status") == LIFECYCLE_POLICY["obsolete_status"]:
        return requirement
    if requirement.get("current_version_id") != expected_current_version_id:
        raise HTTPException(
            status_code=409,
            detail={
                "code": LIFECYCLE_POLICY["revision_conflict_code"],
                "current_version_id": requirement.get("current_version_id"),
            },
        )
    current_version = await requirement_repository.find_version(
        expected_current_version_id, requirement["project_id"], requirement_id
    )
    if (
        not current_version
        or current_version.get("status") not in LIFECYCLE_POLICY["active_version_statuses"]
    ):
        raise HTTPException(
            status_code=409,
            detail={"code": LIFECYCLE_POLICY["version_conflict_code"]},
        )
    version_status = current_version["status"]
    timestamp = now()
    updated = await requirement_repository.mark_requirement_obsolete(
        requirement_id,
        requirement["project_id"],
        expected_current_version_id,
        requirement["status"],
        LIFECYCLE_POLICY["obsolete_status"],
        reason,
        user.id,
        timestamp,
    )
    if not updated:
        raise HTTPException(
            status_code=409,
            detail={"code": LIFECYCLE_POLICY["revision_conflict_code"]},
        )
    version_updated = await requirement_repository.mark_version_obsolete(
        expected_current_version_id,
        requirement["project_id"],
        requirement_id,
        LIFECYCLE_POLICY["active_version_statuses"],
        LIFECYCLE_POLICY["obsolete_status"],
        version_status,
        reason,
        user.id,
        timestamp,
    )
    if not version_updated:
        await requirement_repository.rollback_requirement_obsolete(
            requirement_id,
            requirement["project_id"],
            LIFECYCLE_POLICY["obsolete_status"],
            timestamp,
            requirement["status"],
            now(),
        )
        raise HTTPException(
            status_code=409,
            detail={"code": LIFECYCLE_POLICY["version_conflict_code"]},
        )
    await audit(
        user.id,
        LIFECYCLE_POLICY["obsolete_event"],
        LIFECYCLE_POLICY["requirement_entity"],
        requirement_id,
        requirement["project_id"],
        {"reason": reason, "version_id": expected_current_version_id},
    )
    current_version = await requirement_repository.find_version(
        expected_current_version_id, requirement["project_id"]
    )
    return {**updated, "current_version": current_version}


async def restore_obsolete_requirement(
    requirement_id: str,
    expected_current_version_id: str,
    reason: str,
    user: CurrentUser,
):
    requirement = await get_project_entity(
        LIFECYCLE_POLICY["requirement_collection"],
        requirement_id,
        user,
        LIFECYCLE_POLICY["restore_permission"],
    )
    if requirement.get("status") != LIFECYCLE_POLICY["obsolete_status"]:
        raise HTTPException(
            status_code=409,
            detail={"code": LIFECYCLE_POLICY["not_obsolete_code"]},
        )
    if requirement.get("current_version_id") != expected_current_version_id:
        raise HTTPException(
            status_code=409,
            detail={
                "code": LIFECYCLE_POLICY["revision_conflict_code"],
                "current_version_id": requirement.get("current_version_id"),
            },
        )
    version = await requirement_repository.find_version(
        expected_current_version_id,
        requirement["project_id"],
        requirement_id,
        LIFECYCLE_POLICY["obsolete_status"],
    )
    if not version:
        raise HTTPException(
            status_code=409,
            detail={"code": LIFECYCLE_POLICY["version_conflict_code"]},
        )
    restored_status = requirement.get("status_before_obsolete") or (
        LIFECYCLE_POLICY["baselined_status"]
        if version.get("baselined_at")
        else LIFECYCLE_POLICY["draft_status"]
    )
    restored_version_status = version.get("status_before_obsolete") or restored_status
    if (
        restored_status not in LIFECYCLE_POLICY["active_version_statuses"]
        or restored_version_status not in LIFECYCLE_POLICY["active_version_statuses"]
    ):
        raise HTTPException(
            status_code=409,
            detail={"code": LIFECYCLE_POLICY["restore_state_invalid_code"]},
        )
    timestamp = now()
    version_restored = await requirement_repository.restore_version(
        version["_id"],
        requirement["project_id"],
        requirement_id,
        LIFECYCLE_POLICY["obsolete_status"],
        restored_version_status,
        reason,
        user.id,
        timestamp,
    )
    if not version_restored:
        raise HTTPException(
            status_code=409,
            detail={"code": LIFECYCLE_POLICY["version_conflict_code"]},
        )
    updated = await requirement_repository.restore_requirement(
        requirement_id,
        requirement["project_id"],
        expected_current_version_id,
        LIFECYCLE_POLICY["obsolete_status"],
        restored_status,
        reason,
        user.id,
        timestamp,
    )
    if not updated:
        await requirement_repository.rollback_version_restore(
            version["_id"],
            requirement["project_id"],
            LIFECYCLE_POLICY["obsolete_status"],
            restored_version_status,
            now(),
        )
        raise HTTPException(
            status_code=409,
            detail={"code": LIFECYCLE_POLICY["revision_conflict_code"]},
        )
    await audit(
        user.id,
        LIFECYCLE_POLICY["restored_event"],
        LIFECYCLE_POLICY["requirement_entity"],
        requirement_id,
        requirement["project_id"],
        {"reason": reason, "version_id": version["_id"]},
    )
    restored_version = await requirement_repository.find_version(
        version["_id"], requirement["project_id"]
    )
    return {**updated, "current_version": restored_version}
