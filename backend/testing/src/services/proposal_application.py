from fastapi import HTTPException

from src.core.common import audit, get_project_entity, new_id, now
from src.domain.contracts import TestCaseDraftCreate
from src.repositories.proposal_application import proposal_application_repository
from src.services.domain_policy import domain_policy
from src.services.maintenance_proposal import (
    require_pending_revision,
    update_proposal_acceptance_rate,
)
from src.clients.project_knowledge import index_artifact
from src.services.test_case_records import create_test_case_draft_record, project_test_text


async def approve_maintenance_proposal(
    proposal_id, payload, user, edited=False, expected_project_id=None
):
    maintenance_policy = domain_policy("maintenance_proposal")
    if expected_project_id is not None:
        proposal = await get_project_entity(
            "maintenance_proposals",
            proposal_id,
            user,
            domain_policy("proposal_application")["approve_permission"],
        )
        if proposal["project_id"] != expected_project_id:
            raise HTTPException(
                status_code=422,
                detail={"code": maintenance_policy["project_mismatch_code"]},
            )
    final_status = (
        maintenance_policy["edited_accepted_status"]
        if edited
        else maintenance_policy["accepted_status"]
    )
    return await apply_maintenance_proposal(proposal_id, payload, user, final_status)


async def apply_maintenance_proposal(proposal_id, payload, user, final_status):
    policy = domain_policy("proposal_application")
    proposal = await get_project_entity(
        "maintenance_proposals", proposal_id, user, policy["approve_permission"]
    )
    if proposal.get("status") in policy["accepted_statuses"] and proposal.get(
        "applied_artifact_id"
    ):
        result = await proposal_application_repository.find_applied_artifact(
            proposal["applied_artifact_id"], proposal["project_id"]
        )
        return {"proposal": proposal, "result": result}
    require_pending_revision(proposal, payload, allow_partial=True)
    previous_status = proposal["status"]
    proposal = await proposal_application_repository.transition_proposal(
        proposal_id,
        proposal["project_id"],
        payload.expected_revision,
        previous_status,
        {
            "status": policy["applying_status"],
            "applying_by": user.id,
            "updated_at": now(),
        },
    )
    if not proposal:
        current = await proposal_application_repository.find_proposal(proposal_id)
        if (
            current
            and current.get("status") in policy["accepted_statuses"]
            and current.get("applied_artifact_id")
        ):
            result = await proposal_application_repository.find_applied_artifact(
                current["applied_artifact_id"], current["project_id"]
            )
            return {"proposal": current, "result": result}
        raise HTTPException(
            status_code=409, detail={"code": policy["apply_in_progress_code"]}
        )
    patch = {**proposal.get("patch", {}), **(payload.patch or {})}
    try:
        if previous_status == policy["partial_status"] and proposal.get("partial_version_id"):
            result = await recover_partial_proposal(proposal, user)
        elif proposal["proposal_type"] == policy["create_type"]:
            result = await create_test_draft_from_proposal(proposal, patch, user)
        elif proposal["proposal_type"] == policy["update_type"]:
            result = await create_test_version_from_proposal(proposal, patch, user)
        elif proposal["proposal_type"] == policy["obsolete_type"]:
            result = await mark_test_obsolete(proposal)
        else:
            raise HTTPException(
                status_code=422, detail={"code": policy["unsupported_type_code"]}
            )
    except HTTPException:
        await proposal_application_repository.update_proposal(
            {"_id": proposal_id, "status": policy["applying_status"]},
            {"status": previous_status, "updated_at": now()},
        )
        raise
    except Exception as error:
        partial = await proposal_application_repository.find_proposal(proposal_id)
        if partial and partial.get("partial_version_id"):
            await proposal_application_repository.update_proposal(
                {"_id": proposal_id},
                {
                    "status": policy["partial_status"],
                    "recovery_error": str(error)[: policy["error_length"]],
                    "updated_at": now(),
                },
            )
            raise HTTPException(
                status_code=503,
                detail={
                    "code": policy["apply_partial_code"],
                    "retryable": True,
                    "state_after_failure": policy["partial_status"],
                    "user_action_required": True,
                },
            ) from error
        await proposal_application_repository.update_proposal(
            {"_id": proposal_id, "status": policy["applying_status"]},
            {
                "status": policy["pending_status"],
                "recovery_error": str(error)[: policy["error_length"]],
                "updated_at": now(),
            },
        )
        raise HTTPException(
            status_code=503,
            detail={
                "code": policy["apply_failed_code"],
                "retryable": True,
                "state_after_failure": policy["unchanged_state"],
                "user_action_required": True,
            },
        ) from error
    finalized = await proposal_application_repository.update_proposal(
        {
            "_id": proposal_id,
            "project_id": proposal["project_id"],
            "status": policy["applying_status"],
        },
        {
            "status": final_status,
            "applied_artifact_id": result.get("_id"),
            "review_note": payload.review_note,
            "reviewed_by": user.id,
            "reviewed_at": now(),
            "updated_at": now(),
        },
    )
    if finalized.matched_count != 1:
        await proposal_application_repository.update_proposal(
            {"_id": proposal_id, "project_id": proposal["project_id"]},
            {
                "status": policy["partial_status"],
                "partial_version_id": result.get("_id"),
                "updated_at": now(),
            },
        )
        raise HTTPException(
            status_code=503,
            detail={
                "code": policy["apply_partial_code"],
                "retryable": True,
                "state_after_failure": policy["partial_status"],
                "user_action_required": True,
            },
        )
    await update_proposal_acceptance_rate(proposal["project_id"])
    await audit(
        user.id,
        policy["applied_event"],
        policy["entity_type"],
        proposal_id,
        proposal["project_id"],
        {"result_id": result.get("_id")},
    )
    return {
        "proposal": await proposal_application_repository.find_proposal(proposal_id),
        "result": result,
    }


async def create_test_version_from_proposal(proposal, patch, user):
    policy = domain_policy("proposal_application")
    test_case = await proposal_application_repository.find_test_case(
        proposal["target_artifact_id"], proposal["project_id"]
    )
    if not test_case or test_case.get("current_version_id") != proposal["base_version_id"]:
        raise HTTPException(
            status_code=409,
            detail={
                "code": policy["stale_proposal_code"],
                "current_version_id": test_case.get("current_version_id") if test_case else None,
            },
        )
    base = await proposal_application_repository.find_test_version(
        proposal["base_version_id"]
    )
    allowed = set(policy["patch_fields"])
    merged = {**base, **{key: value for key, value in patch.items() if key in allowed}}
    merged["plain_text_projection"] = project_test_text(merged)
    version = {
        **{
            key: value
            for key, value in merged.items()
            if key
            not in set(policy["version_excluded_fields"])
        },
        "_id": new_id(policy["version_id_prefix"]),
        "version": int(base["version"]) + 1,
        "parent_version_id": base["_id"],
        "change_reason": proposal["reason"],
        "approved_by": user.id,
        "created_at": now(),
    }
    await proposal_application_repository.insert_test_version(version)
    await proposal_application_repository.update_proposal(
        {"_id": proposal["_id"]},
        {
            "partial_version_id": version["_id"],
            "apply_state": policy["version_created_state"],
            "updated_at": now(),
        },
    )
    updated = await proposal_application_repository.activate_test_version(
        test_case["_id"],
        proposal["project_id"],
        proposal["base_version_id"],
        version["_id"],
        policy["active_status"],
        now(),
    )
    if not updated:
        raise RuntimeError(policy["version_conflict_code"])
    await proposal_application_repository.mark_previous_traces(
        proposal["project_id"],
        base["_id"],
        policy["current_trace_statuses"],
        policy["stale_status"],
        now(),
    )
    analysis = await proposal_application_repository.find_impact_analysis(
        proposal["impact_analysis_id"]
    )
    change_set = await proposal_application_repository.find_change_set(
        analysis["change_set_id"]
    )
    await proposal_application_repository.insert_trace(
        {
            "_id": new_id(policy["trace_id_prefix"]),
            "project_id": proposal["project_id"],
            "source_type": policy["requirement_source_type"],
            "source_id": change_set["to_version_id"],
            "target_type": policy["test_version_target_type"],
            "target_id": version["_id"],
            "link_type": policy["trace_link_type"],
            "confidence": policy["manual_confidence"],
            "origin": policy["manual_origin"],
            "status": policy["confirmed_status"],
            "revision": policy["initial_revision"],
            "evidence": proposal["evidence"],
            "created_by": user.id,
            "created_at": now(),
            "updated_at": now(),
        }
    )
    await index_artifact(
        version["project_id"],
        policy["test_version_target_type"],
        version["test_case_id"],
        version["_id"],
        version["title"],
        version["plain_text_projection"],
        version["status"],
        policy["approved_authority"],
        version["version"],
        requirement_version_ids=version.get("requirement_version_ids", []),
        acceptance_criterion_ids=version.get("acceptance_criterion_ids", []),
    )
    return version


async def recover_partial_proposal(proposal, user):
    policy = domain_policy("proposal_application")
    version = await proposal_application_repository.find_test_version(
        proposal["partial_version_id"], proposal["project_id"]
    )
    if not version:
        draft = await proposal_application_repository.find_test_draft(
            proposal["partial_version_id"], proposal["project_id"]
        )
        if draft:
            return draft
        test_case = await proposal_application_repository.find_test_case(
            proposal["partial_version_id"], proposal["project_id"]
        )
        if test_case and proposal.get("proposal_type") == policy["obsolete_type"]:
            await proposal_application_repository.set_test_case_status(
                test_case["_id"],
                proposal["project_id"],
                policy["obsolete_status"],
                now(),
            )
            return await proposal_application_repository.find_test_case(
                test_case["_id"], proposal["project_id"]
            )
    if not version:
        raise HTTPException(
            status_code=409,
            detail={
                "code": policy["partial_artifact_not_found_code"],
                "state_after_failure": policy["partial_status"],
            },
        )
    test_case = await proposal_application_repository.find_test_case(
        proposal["target_artifact_id"], proposal["project_id"]
    )
    if test_case and test_case.get("current_version_id") != version["_id"]:
        await proposal_application_repository.activate_test_version(
            test_case["_id"],
            proposal["project_id"],
            test_case.get("current_version_id"),
            version["_id"],
            policy["active_status"],
            now(),
        )
    analysis = await proposal_application_repository.find_impact_analysis(
        proposal["impact_analysis_id"]
    )
    change_set = (
        await proposal_application_repository.find_change_set(analysis["change_set_id"])
        if analysis
        else None
    )
    if change_set:
        trace = await proposal_application_repository.find_trace(
            {
                "project_id": proposal["project_id"],
                "source_id": change_set["to_version_id"],
                "target_id": version["_id"],
                "status": policy["confirmed_status"],
            }
        )
        if not trace:
            await proposal_application_repository.insert_trace(
                {
                    "_id": new_id(policy["trace_id_prefix"]),
                    "project_id": proposal["project_id"],
                    "source_type": policy["requirement_source_type"],
                    "source_id": change_set["to_version_id"],
                    "target_type": policy["test_version_target_type"],
                    "target_id": version["_id"],
                    "link_type": policy["trace_link_type"],
                    "confidence": policy["manual_confidence"],
                    "origin": policy["manual_origin"],
                    "status": policy["confirmed_status"],
                    "revision": policy["initial_revision"],
                    "evidence": proposal.get("evidence", []),
                    "created_by": user.id,
                    "created_at": now(),
                    "updated_at": now(),
                }
            )
    await index_artifact(
        version["project_id"],
        policy["test_version_target_type"],
        version["test_case_id"],
        version["_id"],
        version["title"],
        version["plain_text_projection"],
        version["status"],
        policy["approved_authority"],
        version["version"],
        requirement_version_ids=version.get("requirement_version_ids", []),
        acceptance_criterion_ids=version.get("acceptance_criterion_ids", []),
    )
    return version


async def create_test_draft_from_proposal(proposal, patch, user):
    policy = domain_policy("proposal_application")
    required = set(policy["required_create_fields"])
    if not required.issubset(patch):
        raise HTTPException(
            status_code=422, detail={"code": policy["incomplete_patch_code"]}
        )
    payload = TestCaseDraftCreate(
        title=patch["title"],
        type=patch.get("type", policy["custom_test_type"]),
        objective_doc=patch.get("objective_doc", policy["empty_document"]),
        preconditions_doc=patch.get("preconditions_doc", policy["empty_document"]),
        steps=patch["steps"],
        test_data=patch.get("test_data", {}),
        expected_result_doc=patch["expected_result_doc"],
        requirement_version_ids=patch.get("requirement_version_ids", []),
        origin=policy["maintenance_origin"],
        source_evidence=proposal["evidence"],
    )
    return await create_test_case_draft_record(proposal["project_id"], payload, user)


async def mark_test_obsolete(proposal):
    policy = domain_policy("proposal_application")
    test_case = await proposal_application_repository.find_test_case(
        proposal["target_artifact_id"], proposal["project_id"]
    )
    if not test_case or test_case.get("current_version_id") != proposal["base_version_id"]:
        raise HTTPException(
            status_code=409, detail={"code": policy["stale_proposal_code"]}
        )
    updated = await proposal_application_repository.mark_test_obsolete(
        test_case["_id"],
        proposal["project_id"],
        proposal["base_version_id"],
        policy["obsolete_status"],
        now(),
    )
    if not updated:
        raise HTTPException(
            status_code=409, detail={"code": policy["stale_proposal_code"]}
        )
    return await proposal_application_repository.find_test_case(
        test_case["_id"], proposal["project_id"]
    )
