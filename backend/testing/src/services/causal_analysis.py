from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now
from src.repositories import causal_analysis_repository
from src.services.causal_analysis_assistance import generate_hypotheses
from src.services.causal_analysis_query import (
    get_analysis,
    list_analyses,
    suggest_candidates,
    validate_member,
)
from src.services.domain_policy import domain_policy

CAUSAL_POLICY = domain_policy("causal_analysis")


async def create_analysis(project_id, payload, user):
    policy = CAUSAL_POLICY
    await get_project(project_id, user, policy["permissions"]["create"])
    defect_ids = list(dict.fromkeys(payload.defect_ids))
    if defect_ids:
        defects = await causal_analysis_repository.list_defects(
            {"_id": {"$in": defect_ids}, "project_id": project_id},
            policy["analysis_limit"],
        )
        if len(defects) != len(defect_ids):
            raise HTTPException(
                status_code=422,
                detail={"code": policy["error_codes"]["defect_not_in_project"]},
            )
    await validate_member(project_id, payload.owner_id)
    if payload.idempotency_key:
        existing = await causal_analysis_repository.find_analysis_by_idempotency(
            project_id, payload.idempotency_key
        )
        if existing:
            if set(existing.get("defect_ids", [])) != set(defect_ids):
                raise HTTPException(
                    status_code=409,
                    detail={"code": policy["error_codes"]["idempotency_reused"]},
                )
            return existing
    timestamp = now()
    identifier = new_id(policy["analysis_id_prefix"])
    data = payload.model_dump(exclude={"evidence"})
    value = {
        "_id": identifier,
        "analysis_key": identifier,
        "project_id": project_id,
        **data,
        "defect_ids": defect_ids,
        "root_causes": [],
        "contributing_factors": [],
        "five_whys": [],
        "corrective_actions": [],
        "preventive_actions": [],
        "approved_by": None,
        "effectiveness_reviews": [],
        "status": policy["draft_status"],
        "revision": policy["initial_revision"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await causal_analysis_repository.insert_analysis(value)
    except DuplicateKeyError:
        if payload.idempotency_key:
            return await causal_analysis_repository.find_analysis_by_idempotency(
                project_id, payload.idempotency_key
            )
        raise
    await audit(
        user.id,
        policy["events"]["created"],
        policy["entity_types"]["analysis"],
        value["_id"],
        project_id,
        {"defect_ids": defect_ids},
    )
    return value


async def update_analysis(analysis_id, payload, user):
    policy = CAUSAL_POLICY
    value = await get_analysis(analysis_id, user, policy["permissions"]["update"])
    if value["status"] != policy["draft_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["not_draft"]})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    if "owner_id" in changes:
        await validate_member(value["project_id"], changes["owner_id"])
    changes["updated_at"] = now()
    updated = await causal_analysis_repository.update_analysis(
        {
            "_id": analysis_id,
            "revision": payload.expected_revision,
            "status": policy["draft_status"],
        },
        changes,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["revision_conflict"]})
    await audit(
        user.id,
        policy["events"]["updated"],
        policy["entity_types"]["analysis"],
        analysis_id,
        value["project_id"],
        {"fields": sorted(changes)},
    )
    return updated


async def link_defects(analysis_id, payload, user):
    policy = CAUSAL_POLICY
    value = await get_analysis(analysis_id, user, policy["permissions"]["update"])
    if value["status"] != policy["draft_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["not_draft"]})
    defect_ids = list(dict.fromkeys(payload.defect_ids))
    defects = await causal_analysis_repository.list_defects(
        {"_id": {"$in": defect_ids}, "project_id": value["project_id"]},
        policy["analysis_limit"],
    )
    if len(defects) != len(defect_ids):
        raise HTTPException(status_code=422, detail={"code": policy["error_codes"]["defect_not_in_project"]})
    linked = list(dict.fromkeys([*value.get("defect_ids", []), *defect_ids]))
    updated = await causal_analysis_repository.update_analysis(
        {
            "_id": analysis_id,
            "revision": payload.expected_revision,
            "status": policy["draft_status"],
        },
        {"defect_ids": linked, "updated_at": now()},
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["revision_conflict"]})
    await audit(
        user.id,
        policy["events"]["defects_linked"],
        policy["entity_types"]["analysis"],
        analysis_id,
        value["project_id"],
        {"defect_ids": defect_ids},
    )
    return updated


async def add_five_why(analysis_id, payload, user):
    policy = CAUSAL_POLICY
    value = await get_analysis(analysis_id, user, policy["permissions"]["update"])
    if value["status"] != policy["draft_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["not_draft"]})
    five_whys = list(value.get("five_whys", []))
    if len(five_whys) >= policy["maximum_five_whys"]:
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["five_whys_limit"]})
    five_whys.append(payload.why)
    updated = await causal_analysis_repository.update_analysis(
        {
            "_id": analysis_id,
            "revision": payload.expected_revision,
            "status": policy["draft_status"],
        },
        {"five_whys": five_whys, "updated_at": now()},
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["revision_conflict"]})
    await audit(
        user.id,
        policy["events"]["five_why_added"],
        policy["entity_types"]["analysis"],
        analysis_id,
        value["project_id"],
        {"sequence": len(five_whys)},
    )
    return updated


async def record_root_cause(analysis_id, payload, user):
    policy = CAUSAL_POLICY
    value = await get_analysis(analysis_id, user, policy["permissions"]["update"])
    if value["status"] != policy["draft_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["not_draft"]})
    root_cause = {
        "category": payload.category,
        "detail": payload.detail,
        "evidence_refs": payload.evidence_refs,
        "recorded_by": user.id,
        "recorded_at": now(),
    }
    updated = await causal_analysis_repository.update_analysis(
        {
            "_id": analysis_id,
            "revision": payload.expected_revision,
            "status": policy["draft_status"],
        },
        {
            "root_causes": [root_cause],
            "contributing_factors": payload.contributing_factors,
            "updated_at": now(),
        },
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["revision_conflict"]})
    await audit(
        user.id,
        policy["events"]["root_cause_recorded"],
        policy["entity_types"]["analysis"],
        analysis_id,
        value["project_id"],
        {"category": payload.category},
    )
    return updated


async def create_action(analysis_id, payload, user, action_type):
    policy = CAUSAL_POLICY
    value = await get_analysis(analysis_id, user, policy["permissions"]["action_manage"])
    if value["status"] not in {
        policy["approved_status"],
        policy["action_in_progress_status"],
    }:
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["not_approved"]})
    if value["status"] == policy["closed_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["closed_immutable"]})
    timestamp = now()
    action = {
        "_id": new_id(policy["action_id_prefix"]),
        "causal_analysis_id": analysis_id,
        "project_id": value["project_id"],
        **payload.model_dump(),
        "action_type": action_type,
        "owner_id": None,
        "status": policy["open_action_status"],
        "result": "",
        "revision": policy["initial_revision"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    await causal_analysis_repository.insert_action(action)
    field = (
        policy["corrective_action_field"]
        if action_type == policy["corrective_action_type"]
        else policy["preventive_action_field"]
    )
    analysis = await causal_analysis_repository.update_analysis(
        {
            "_id": analysis_id,
            "revision": value["revision"],
            "status": {
                "$in": [policy["approved_status"], policy["action_in_progress_status"]]
            },
        },
        {"status": policy["action_in_progress_status"], "updated_at": timestamp},
        {field: action["_id"]},
    )
    if not analysis:
        await causal_analysis_repository.delete_action(action["_id"])
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["revision_conflict"]})
    await audit(
        user.id,
        policy["events"]["action_created"],
        policy["entity_types"]["action"],
        action["_id"],
        value["project_id"],
        {"causal_analysis_id": analysis_id, "type": action_type},
    )
    return action


async def assign_action(action_id, payload, user):
    policy = CAUSAL_POLICY
    action = await causal_analysis_repository.find_action(action_id)
    if not action:
        raise HTTPException(status_code=404, detail={"code": policy["error_codes"]["entity_not_found"]})
    await get_project(action["project_id"], user, policy["permissions"]["action_manage"])
    await validate_member(action["project_id"], payload.owner_id)
    if action["status"] == policy["closed_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["action_closed"]})
    timestamp = now()
    updated = await causal_analysis_repository.update_action(
        {
            "_id": action_id,
            "revision": payload.expected_revision,
            "status": {"$ne": policy["closed_status"]},
        },
        {
            "owner_id": payload.owner_id,
            "assigned_by": user.id,
            "assigned_at": timestamp,
            "updated_at": timestamp,
        },
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["revision_conflict"]})
    await audit(
        user.id,
        policy["events"]["action_assigned"],
        policy["entity_types"]["action"],
        action_id,
        action["project_id"],
        {"owner_id": payload.owner_id},
    )
    return updated


async def update_action(action_id, payload, user):
    policy = CAUSAL_POLICY
    action = await causal_analysis_repository.find_action(action_id)
    if not action:
        raise HTTPException(status_code=404, detail={"code": policy["error_codes"]["entity_not_found"]})
    await get_project(action["project_id"], user, policy["permissions"]["action_manage"])
    if payload.status != policy["open_action_status"] and not action.get("owner_id"):
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["action_owner_required"]})
    states = policy["action_states"]
    if (
        states.index(payload.status) < states.index(action["status"])
        or states.index(payload.status) > states.index(action["status"]) + 1
    ):
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["invalid_action_transition"]})
    changes = {"status": payload.status, "result": payload.result, "updated_at": now()}
    if payload.evidence_refs is not None:
        changes["evidence_refs"] = payload.evidence_refs
    updated = await causal_analysis_repository.update_action(
        {"_id": action_id, "revision": payload.expected_revision, "status": action["status"]},
        changes,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["revision_conflict"]})
    event = (
        policy["events"]["action_closed"]
        if payload.status == policy["closed_status"]
        else policy["events"]["action_updated"]
    )
    await audit(
        user.id,
        event,
        policy["entity_types"]["action"],
        action_id,
        action["project_id"],
        {"from": action["status"], "to": payload.status},
    )
    return updated


async def submit_review(analysis_id, payload, user):
    policy = CAUSAL_POLICY
    value = await get_analysis(analysis_id, user, policy["permissions"]["update"])
    if not value.get("defect_ids"):
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["defect_required"]})
    if not value.get("five_whys"):
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["five_whys_required"]})
    if not value.get("root_causes"):
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["root_cause_required"]})
    timestamp = now()
    updated = await causal_analysis_repository.update_analysis(
        {
            "_id": analysis_id,
            "revision": payload.expected_revision,
            "status": policy["draft_status"],
        },
        {
            "status": policy["review_status"],
            "submitted_by": user.id,
            "submitted_at": timestamp,
            "review_note": payload.note,
            "updated_at": timestamp,
        },
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["submit_conflict"]})
    await audit(
        user.id,
        policy["events"]["submitted"],
        policy["entity_types"]["analysis"],
        analysis_id,
        value["project_id"],
        {"note": payload.note},
    )
    return updated


async def approve_analysis(analysis_id, payload, user):
    policy = CAUSAL_POLICY
    value = await get_analysis(analysis_id, user, policy["permissions"]["approve"])
    target = (
        policy["approved_status"]
        if payload.decision == policy["approve_decision"]
        else policy["draft_status"]
    )
    timestamp = now()
    changes = {
        "status": target,
        "approval_note": payload.note,
        "reviewed_by": user.id,
        "reviewed_at": timestamp,
        "updated_at": timestamp,
    }
    if target == policy["approved_status"]:
        changes.update({"approved_by": user.id, "approved_at": timestamp})
    else:
        changes.update({"approved_by": None, "approved_at": None})
    updated = await causal_analysis_repository.update_analysis(
        {
            "_id": analysis_id,
            "revision": payload.expected_revision,
            "status": policy["review_status"],
        },
        changes,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["review_conflict"]})
    event = (
        policy["events"]["approved"]
        if target == policy["approved_status"]
        else policy["events"]["reviewed"]
    )
    await audit(
        user.id,
        event,
        policy["entity_types"]["analysis"],
        analysis_id,
        value["project_id"],
        {"decision": payload.decision},
    )
    return updated


async def review_effectiveness(analysis_id, payload, user):
    policy = CAUSAL_POLICY
    value = await get_analysis(analysis_id, user, policy["permissions"]["update"])
    if value["status"] != policy["action_in_progress_status"]:
        raise HTTPException(
            status_code=409, detail={"code": policy["error_codes"]["actions_not_in_progress"]}
        )
    actions = await causal_analysis_repository.list_actions(
        analysis_id, policy["action_limit"]
    )
    if not actions or any(
        item["status"] not in policy["implemented_action_statuses"] for item in actions
    ):
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["actions_not_implemented"]})
    review = {
        "decision": payload.decision,
        "result": payload.result,
        "evidence_refs": payload.evidence_refs,
        "reviewed_at": payload.reviewed_at,
        "reviewed_by": user.id,
    }
    reviews = [*value.get("effectiveness_reviews", []), review]
    target = (
        policy["effectiveness_review_status"]
        if payload.decision == policy["effective_decision"]
        else policy["action_in_progress_status"]
    )
    updated = await causal_analysis_repository.update_analysis(
        {
            "_id": analysis_id,
            "revision": payload.expected_revision,
            "status": policy["action_in_progress_status"],
        },
        {
            "status": target,
            "effectiveness_reviews": reviews,
            "effectiveness_review_at": payload.reviewed_at,
            "updated_at": now(),
        },
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["revision_conflict"]})
    await audit(
        user.id,
        policy["events"]["effectiveness_reviewed"],
        policy["entity_types"]["analysis"],
        analysis_id,
        value["project_id"],
        {"decision": payload.decision, "evidence_refs": payload.evidence_refs},
    )
    return updated


async def close_analysis(analysis_id, payload, user):
    policy = CAUSAL_POLICY
    value = await get_analysis(analysis_id, user, policy["permissions"]["approve"])
    actions = await causal_analysis_repository.list_actions(
        analysis_id, policy["action_limit"]
    )
    if not actions or any(item["status"] != policy["closed_status"] for item in actions):
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["actions_not_closed"]})
    if (
        not value.get("effectiveness_reviews")
        or value["effectiveness_reviews"][-1].get("decision")
        != policy["effective_decision"]
    ):
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["effectiveness_approval_required"]})
    timestamp = now()
    updated = await causal_analysis_repository.update_analysis(
        {
            "_id": analysis_id,
            "revision": payload.expected_revision,
            "status": policy["effectiveness_review_status"],
        },
        {
            "status": policy["closed_status"],
            "closed_by": user.id,
            "closed_at": timestamp,
            "close_note": payload.note,
            "updated_at": timestamp,
        },
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["error_codes"]["close_conflict"]})
    await audit(
        user.id,
        policy["events"]["closed"],
        policy["entity_types"]["analysis"],
        analysis_id,
        value["project_id"],
        {"note": payload.note},
    )
    return updated


class CausalAnalysisService:
    @staticmethod
    async def list(project_id, user):
        return await list_analyses(project_id, user)

    @staticmethod
    async def candidates(project_id, user):
        return await suggest_candidates(project_id, user)

    @staticmethod
    async def create(project_id, payload, user):
        return await create_analysis(project_id, payload, user)

    @staticmethod
    async def get(analysis_id, user):
        policy = CAUSAL_POLICY
        value = await get_analysis(analysis_id, user)
        value["actions"] = await causal_analysis_repository.list_actions(
            analysis_id, policy["action_limit"]
        )
        return value

    @staticmethod
    async def update(analysis_id, payload, user):
        return await update_analysis(analysis_id, payload, user)

    @staticmethod
    async def link_defects(analysis_id, payload, user):
        return await link_defects(analysis_id, payload, user)

    @staticmethod
    async def add_five_why(analysis_id, payload, user):
        return await add_five_why(analysis_id, payload, user)

    @staticmethod
    async def record_root_cause(analysis_id, payload, user):
        return await record_root_cause(analysis_id, payload, user)

    @staticmethod
    async def create_action(analysis_id, payload, user, action_type):
        return await create_action(analysis_id, payload, user, action_type)

    @staticmethod
    async def assign_action(action_id, payload, user):
        return await assign_action(action_id, payload, user)

    @staticmethod
    async def update_action(action_id, payload, user):
        return await update_action(action_id, payload, user)

    @staticmethod
    async def submit_review(analysis_id, payload, user):
        return await submit_review(analysis_id, payload, user)

    @staticmethod
    async def approve(analysis_id, payload, user):
        return await approve_analysis(analysis_id, payload, user)

    @staticmethod
    async def review_effectiveness(analysis_id, payload, user):
        return await review_effectiveness(analysis_id, payload, user)

    @staticmethod
    async def close(analysis_id, payload, user):
        return await close_analysis(analysis_id, payload, user)

    @staticmethod
    async def generate_hypotheses(analysis_id, payload, user):
        return await generate_hypotheses(analysis_id, payload, user)
