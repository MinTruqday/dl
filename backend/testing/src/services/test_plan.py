import hashlib
import json
import re

from fastapi import HTTPException

from src.core.common import (
    audit,
    get_project,
    get_project_entity,
    new_id,
    now,
    optimistic_patch,
    require_action_policy,
    sort_spec,
)
from src.domain.contracts import TestPlanCreate
from src.repositories import test_plan_repository
from src.services.domain_policy import domain_policy
from src.services.execution_context import resolve_execution_context


def plan_snapshot(plan):
    return {
        field: plan.get(field)
        for field in domain_policy("test_plan")["snapshot_fields"]
    }


def plan_snapshot_hash(plan):
    canonical = json.dumps(
        plan_snapshot(plan), ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def plan_completeness(plan, settings=None):
    settings = settings or {}
    policy = domain_policy("test_plan")
    checks = [
        (
            policy["strategy_requirement"]["code"],
            all(plan.get(field) for field in policy["strategy_requirement"]["fields"]),
        ),
        *[
            (requirement["code"], bool(plan.get(requirement["field"])))
            for requirement in policy["required_fields"]
        ],
        (
            policy["schedule_requirement"]["code"],
            all(
                (plan.get(policy["schedule_requirement"]["field"]) or {}).get(field)
                for field in policy["schedule_requirement"]["required_fields"]
            ),
        ),
    ]
    for requirement in policy["conditional_requirements"]:
        if settings.get(requirement["setting"], requirement["default"]):
            checks.append((requirement["code"], bool(plan.get(requirement["field"]))))
    findings = [
        {"code": code, "severity": policy["finding_severity"]}
        for code, passed in checks
        if not passed
    ]
    return {"ready_for_approval": not findings, "findings": findings}


async def resolve_strategy_binding(project_id, strategy_version_id, auto_bind=False):
    policy = domain_policy("test_plan")
    strategy = None
    if strategy_version_id:
        strategy = await test_plan_repository.find_strategy(
            project_id, strategy_version_id
        )
        if not strategy:
            raise HTTPException(status_code=422, detail={"code": policy["invalid_strategy_code"]})
        if strategy.get("status") != policy["approved_status"] or not strategy.get(
            "snapshot_hash"
        ):
            raise HTTPException(
                status_code=409, detail={"code": policy["strategy_not_approved_code"]}
            )
    elif auto_bind:
        strategy = await test_plan_repository.find_active_strategy(
            project_id, policy["approved_status"]
        )
    if not strategy:
        return {
            "strategy_version_id": None,
            "strategy_id": None,
            "strategy_version": None,
            "strategy_snapshot_hash": None,
        }
    return {
        "strategy_version_id": strategy["_id"],
        "strategy_id": strategy["lineage_id"],
        "strategy_version": strategy["version"],
        "strategy_snapshot_hash": strategy["snapshot_hash"],
    }


async def create_test_plan_record(payload, project_id, user):
    policy = domain_policy("test_plan")
    if project_id and project_id != payload.project_id:
        raise HTTPException(status_code=422, detail={"code": policy["project_scope_mismatch_code"]})
    await get_project(payload.project_id, user, "testplan.create")
    context = await resolve_execution_context(
        payload.project_id,
        user,
        release_id=payload.release_id,
        build_id=payload.build_id,
        environment_id=payload.environment_id,
        release=payload.release,
        build=payload.build,
        environment=payload.environment,
    )
    if payload.members:
        await require_action_policy(
            payload.project_id,
            user,
            "testplan.assignments",
            set(policy["assignment_roles"]),
        )
    strategy_binding = await resolve_strategy_binding(
        payload.project_id,
        payload.strategy_version_id,
        auto_bind=True,
    )
    timestamp = now()
    plan = {
        "_id": new_id(policy["id_prefix"]),
        **payload.model_dump(),
        **context,
        **strategy_binding,
        "status": policy["draft_status"],
        "approval_history": [],
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    await test_plan_repository.insert_plan(plan)
    await audit(user.id, "test_plan_created", "TestPlan", plan["_id"], payload.project_id)
    return plan


async def list_test_plan_records(
    project_id,
    user,
    q="",
    release="",
    release_id="",
    build_id="",
    environment_id="",
    status="",
    sort="-updated_at",
):
    policy = domain_policy("test_plan")
    await get_project(project_id, user, "testplan.read")
    query = {"project_id": project_id}
    if q:
        query["$or"] = [
            {"name": {"$regex": re.escape(q), "$options": "i"}},
            {"objective": {"$regex": re.escape(q), "$options": "i"}},
        ]
    for field, value in {
        "release": release,
        "release_id": release_id,
        "build_id": build_id,
        "environment_id": environment_id,
        "status": status,
    }.items():
        if value:
            query[field] = value
    sort_field, direction = sort_spec(
        sort,
        set(policy["sort_fields"]),
    )
    return await test_plan_repository.list_plans(
        query, sort_field, direction, policy["list_limit"]
    )


async def get_test_plan_record(plan_id, user, permission="testplan.read"):
    return await get_project_entity("test_plans", plan_id, user, permission)


async def validate_test_plan_record(plan_id, user):
    plan = await get_test_plan_record(plan_id, user, "testplan.review")
    settings = await test_plan_repository.find_project_settings(plan["project_id"])
    return plan_completeness(plan, settings)


async def update_test_plan_record(plan_id, payload, user):
    policy = domain_policy("test_plan")
    plan = await get_test_plan_record(plan_id, user, "testplan.update")
    if plan.get("status") != policy["draft_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["not_draft_code"]})
    if payload.members is not None:
        await require_action_policy(
            plan["project_id"],
            user,
            "testplan.assignments",
            set(policy["assignment_roles"]),
        )
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    if "strategy_version_id" in changes:
        changes.update(
            await resolve_strategy_binding(
                plan["project_id"],
                changes.get("strategy_version_id"),
                auto_bind=False,
            )
        )
    if {"release_id", "build_id", "environment_id", "release", "build", "environment"} & set(
        changes
    ):
        changes.update(
            await resolve_execution_context(
                plan["project_id"],
                user,
                release_id=changes.get("release_id", plan.get("release_id")),
                build_id=changes.get("build_id", plan.get("build_id")),
                environment_id=changes.get("environment_id", plan.get("environment_id")),
                release=changes.get("release", plan.get("release", "")),
                build=changes.get("build", plan.get("build", "")),
                environment=changes.get("environment", plan.get("environment", "")),
            )
        )
    validation_data = {}
    for field in TestPlanCreate.model_fields:
        if field in changes:
            validation_data[field] = changes[field]
        elif field in plan:
            validation_data[field] = plan[field]
    TestPlanCreate.model_validate(validation_data)
    updated = await optimistic_patch(
        "test_plans",
        plan_id,
        plan["project_id"],
        payload.expected_revision,
        changes,
    )
    await audit(user.id, "test_plan_updated", "TestPlan", plan_id, plan["project_id"])
    return updated


async def submit_test_plan_record(plan_id, payload, user):
    policy = domain_policy("test_plan")
    plan = await get_test_plan_record(plan_id, user, "testplan.submit_review")
    if plan.get("status") != policy["draft_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["invalid_transition_code"]})
    updated = await optimistic_patch(
        "test_plans",
        plan_id,
        plan["project_id"],
        payload.expected_revision,
        {"status": policy["review_status"], "review_note": payload.review_note},
    )
    await audit(user.id, "test_plan_submitted", "TestPlan", plan_id, plan["project_id"])
    return updated


async def approve_test_plan_record(plan_id, payload, user):
    policy = domain_policy("test_plan")
    plan = await get_test_plan_record(plan_id, user, "testplan.approve")
    if plan.get("status") not in policy["approval_source_statuses"]:
        raise HTTPException(status_code=409, detail={"code": policy["invalid_transition_code"]})
    settings = await test_plan_repository.find_project_settings(plan["project_id"])
    if settings.get("strict_test_plan_approval", False):
        completeness = plan_completeness(plan, settings)
        if not completeness["ready_for_approval"]:
            raise HTTPException(
                status_code=409,
                detail={"code": policy["incomplete_code"], **completeness},
            )
    timestamp = now()
    approved_hash = plan_snapshot_hash(plan)
    approval = {
        "actor_id": user.id,
        "action": policy["approved_status"],
        "note": payload.review_note,
        "at": timestamp,
    }
    updated = await optimistic_patch(
        "test_plans",
        plan_id,
        plan["project_id"],
        payload.expected_revision,
        {
            "status": policy["approved_status"],
            "approved_by": user.id,
            "approved_at": timestamp,
            "approved_snapshot": plan_snapshot(plan),
            "approved_snapshot_hash": approved_hash,
            "baseline_hash": approved_hash,
            "approval_history": [*plan.get("approval_history", []), approval],
            "review_note": payload.review_note,
        },
    )
    await audit(user.id, "test_plan_approved", "TestPlan", plan_id, plan["project_id"])
    return updated


async def archive_test_plan_record(plan_id, payload, user):
    policy = domain_policy("test_plan")
    plan = await get_test_plan_record(plan_id, user, "testplan.archive")
    updated = await optimistic_patch(
        "test_plans",
        plan_id,
        plan["project_id"],
        payload.expected_revision,
        {
            "status": policy["archived_status"],
            "archive_reason": payload.reason,
            "archived_by": user.id,
            "archived_at": now(),
        },
    )
    await audit(user.id, "test_plan_archived", "TestPlan", plan_id, plan["project_id"])
    return updated


async def clone_test_plan_record(plan_id, user):
    policy = domain_policy("test_plan")
    plan = await get_test_plan_record(plan_id, user, "testplan.create")
    timestamp = now()
    cloned = {
        **plan,
        "_id": new_id(policy["id_prefix"]),
        "name": f"{plan['name']}{policy['clone_name_suffix']}",
        "status": policy["draft_status"],
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    for field in (
        "approved_at",
        "approved_by",
        "approved_snapshot",
        "approved_snapshot_hash",
        "baseline_hash",
        "approval_history",
        "archived_at",
        "archived_by",
        "archive_reason",
        "reviewed_at",
        "reviewed_by",
    ):
        cloned.pop(field, None)
    cloned["approval_history"] = []
    await test_plan_repository.insert_plan(cloned)
    await audit(
        user.id,
        "test_plan_cloned",
        "TestPlan",
        cloned["_id"],
        plan["project_id"],
        {"source_plan_id": plan_id},
    )
    return cloned
