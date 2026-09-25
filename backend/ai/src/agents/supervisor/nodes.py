from datetime import datetime, timezone

from src.agents.specialist import specialists
from src.agents.supervisor.policy import available_tools, fallback_tasks, validated_tasks
from src.knowledge.evidence import package
from src.knowledge.hybrid import hybrid_evidence
from src.prompts.agents import (
    aggregate_prompt,
    supervisor_plan_prompt,
    supervisor_review_prompt,
)
from src.runtime.limits import limits
from src.runtime.models import (
    AgentApprovalStatus,
    AgentResult,
    AgentRunStatus,
    AgentTaskStatus,
    AgentTask,
    EvidenceItem,
    SupervisorPlan,
    SupervisorProposal,
    SupervisorReview,
    ToolExecutionStatus,
    VeriqRunState,
)
from src.runtime.output import normalize_narrative, normalize_narratives
from src.services.inference import structured
from src.tools.registry import audit_arguments, invoke_tool, policies, verify_application


def state_run(state):
    return VeriqRunState(**state["run"])


async def load_context(state):
    run = state_run(state)
    if run.approval_status in {
        AgentApprovalStatus.APPROVED,
        AgentApprovalStatus.REJECTED,
    } and state.get("tasks"):
        return {}
    supplied = [EvidenceItem(**item) for item in state.get("evidence", [])]
    retrieved = await hybrid_evidence(
        run.project_id,
        run.objective,
        run.user_id,
        state.get("token"),
    )
    verified_refs = {
        item.artifact_version_id or item.artifact_id for item in retrieved.items
    }
    supplied = [
        item
        for item in supplied
        if item.project_id == run.project_id
        and (item.artifact_version_id or item.artifact_id) in verified_refs
    ]
    combined = package(
        run.project_id,
        run.objective,
        [*supplied, *retrieved.items],
        retrieved.degraded_flags,
    )
    run.evidence_refs = list(
        dict.fromkeys(item.artifact_version_id or item.artifact_id for item in combined.items)
    )
    run.observations.append(
        {
            "phase": "LOAD_CONTEXT",
            "evidence_count": len(combined.items),
            "degraded_flags": combined.degraded_flags,
        }
    )
    run.updated_at = datetime.now(timezone.utc)
    return {
        "run": run.model_dump(mode="python"),
        "evidence": [item.model_dump(mode="python") for item in combined.items],
        "degraded_flags": combined.degraded_flags,
    }


def route_after_context(state):
    run = state_run(state)
    if run.approval_status == AgentApprovalStatus.APPROVED and state.get("tasks"):
        return "apply"
    if run.approval_status == AgentApprovalStatus.REJECTED and state.get("tasks"):
        return "re_evaluate"
    return "plan"


async def plan(state):
    run = state_run(state)
    evidence_refs = [
        item.get("artifact_version_id") or item.get("artifact_id")
        for item in state.get("evidence", [])
    ]
    prompt = supervisor_plan_prompt(
        run.project_id,
        run.run_id,
        run.objective,
        run.intent,
        state.get("target_artifact_ids", []),
        available_tools(run.permissions, run.intent),
        evidence_refs,
        state.get("constraints", {}),
    )
    try:
        generated = await structured(
            prompt,
            SupervisorPlan,
            max_tokens=1600,
            timeout_seconds=limits.task_timeout_seconds,
        )
    except Exception:
        run.intent = run.intent or "project_question"
        run.status = AgentRunStatus.RUNNING
        run.current_step = 1
        run.observations.append(
            {"phase": "PLAN", "reason_code": "AI_PROVIDER_UNAVAILABLE"}
        )
        result = AgentResult(
            task_id=f"PLAN-{run.run_id}",
            status=AgentTaskStatus.INSUFFICIENT_EVIDENCE,
            summary="The AI provider is unavailable so a plan cannot be created",
            evidence_refs=evidence_refs,
            reason_codes=["AI_PROVIDER_UNAVAILABLE"],
            warnings=["AI_PROVIDER_UNAVAILABLE", "MANUAL_REVIEW_REQUIRED"],
        )
        return {
            "run": run.model_dump(mode="python"),
            "tasks": [],
            "success_criteria": [],
            "task_index": 0,
            "results": [result.model_dump(mode="python")],
        }
    allowed_identifiers = list(
        dict.fromkeys(
            [
                *evidence_refs,
                *state.get("target_artifact_ids", []),
                *[
                    item.get("artifact_id")
                    for item in state.get("evidence", [])
                    if item.get("artifact_id")
                ],
            ]
        )
    )
    run.intent = run.intent or generated.intent
    tasks = validated_tasks(
        generated.tasks,
        run,
        evidence_refs,
        known_identifiers=allowed_identifiers,
    )
    tasks = [task for task in tasks if task.tool_calls]
    fallback_applied = False
    if not tasks:
        grounded_tasks = validated_tasks(
            fallback_tasks(
                run,
                evidence_refs,
                state.get("constraints", {}),
            ),
            run,
            evidence_refs,
            known_identifiers=allowed_identifiers,
        )
        if grounded_tasks:
            tasks = grounded_tasks
            fallback_applied = True
    if fallback_applied:
        run.observations.append(
            {"phase": "PLAN", "reason_code": "ROUTING_FALLBACK_APPLIED"}
        )
    results = []
    if not tasks:
        results.append(
            AgentResult(
                task_id=f"PLAN-{run.run_id}",
                status=AgentTaskStatus.FAILED,
                summary="The plan contains no valid task",
                evidence_refs=evidence_refs,
                reason_codes=["VALIDATION_FAILED"],
                warnings=["MANUAL_REVIEW_REQUIRED"],
            ).model_dump(mode="python")
        )
    run.supervisor_plan = [task.model_dump(mode="json") for task in tasks]
    run.status = AgentRunStatus.RUNNING
    run.current_step = 1
    return {
        "run": run.model_dump(mode="python"),
        "tasks": [task.model_dump(mode="python") for task in tasks],
        "success_criteria": generated.success_criteria,
        "task_index": 0,
        "results": results,
    }


async def execute_specialist(state):
    run = state_run(state)
    tasks = [AgentTask(**item) for item in state.get("tasks", [])]
    index = int(state.get("task_index", 0))
    if index >= len(tasks):
        return {}
    task = tasks[index]
    run.active_task = task.model_dump(mode="json")
    evidence_by_ref = {
        item.get("artifact_version_id") or item.get("artifact_id"): item
        for item in state.get("evidence", [])
    }
    task_evidence = [
        EvidenceItem(**evidence_by_ref[reference])
        for reference in task.evidence_refs
        if reference in evidence_by_ref
    ]
    if not task_evidence:
        task_evidence = [EvidenceItem(**item) for item in state.get("evidence", [])]
    result, observations = await specialists[task.specialist].execute(
        task,
        task_evidence,
        run.permissions,
        state["token"],
        run.approval_status,
    )
    run.completed_tasks.append(task.model_dump(mode="json"))
    run.specialist_results.append(result.model_dump(mode="json"))
    run.observations.extend(observations)
    run.tool_calls.extend(
        {
            "task_id": task.task_id,
            "tool_name": item.tool_name,
            "arguments": audit_arguments(item.arguments),
        }
        for item in task.tool_calls
    )
    run.active_task = None
    run.current_step += 1
    return {
        "run": run.model_dump(mode="python"),
        "task_index": index + 1,
        "results": [*state.get("results", []), result.model_dump(mode="python")],
    }


def route_after_specialist(state):
    return "execute" if int(state.get("task_index", 0)) < len(state.get("tasks", [])) else "review"


async def re_evaluate(state):
    run = state_run(state)
    results = [AgentResult(**item) for item in state.get("results", [])]
    if not state.get("tasks"):
        reason_codes = list(
            dict.fromkeys(code for item in results for code in item.reason_codes)
        )
        run.observations.append(
            {
                "phase": "RE_EVALUATE",
                "goal_complete": True,
                "reason_codes": reason_codes,
                "new_task_count": 0,
            }
        )
        return {"run": run.model_dump(mode="python"), "review_complete": True}
    remaining = max(0, limits.supervisor_steps - len(run.completed_tasks))
    if remaining == 0:
        run.observations.append(
            {"phase": "RE_EVALUATE", "reason_code": "AGENT_LIMIT_REACHED"}
        )
        return {"run": run.model_dump(mode="python"), "review_complete": True}
    prompt = supervisor_review_prompt(
        run.objective,
        state.get("success_criteria", []),
        [item.model_dump(mode="json") for item in results],
        available_tools(run.permissions, run.intent, compact=True),
        run.evidence_refs,
        remaining,
    )
    try:
        review = await structured(
            prompt,
            SupervisorReview,
            max_tokens=1400,
            timeout_seconds=limits.task_timeout_seconds,
        )
    except Exception:
        review = SupervisorReview(
            goal_complete=True,
            success_criteria=state.get("success_criteria", []),
            reason_codes=["AI_PROVIDER_UNAVAILABLE"],
        )
    allowed_identifiers = list(
        dict.fromkeys(
            [
                *run.evidence_refs,
                *state.get("target_artifact_ids", []),
                *[
                    item.get("artifact_id")
                    for item in state.get("evidence", [])
                    if item.get("artifact_id")
                ],
            ]
        )
    )
    new_tasks = validated_tasks(
        review.tasks,
        run,
        run.evidence_refs,
        remaining,
        allowed_identifiers,
    )
    new_tasks = [task for task in new_tasks if task.tool_calls]
    existing = {
        (item.get("specialist"), item.get("objective")) for item in state.get("tasks", [])
    }
    new_tasks = [
        item for item in new_tasks if (item.specialist, item.objective) not in existing
    ]
    complete = review.goal_complete or not new_tasks
    run.observations.append(
        {
            "phase": "RE_EVALUATE",
            "goal_complete": complete,
            "reason_codes": review.reason_codes,
            "new_task_count": len(new_tasks),
        }
    )
    if complete:
        return {
            "run": run.model_dump(mode="python"),
            "review_complete": True,
            "success_criteria": review.success_criteria or state.get("success_criteria", []),
        }
    combined = [*state.get("tasks", []), *[item.model_dump(mode="python") for item in new_tasks]]
    run.supervisor_plan.extend(item.model_dump(mode="json") for item in new_tasks)
    return {
        "run": run.model_dump(mode="python"),
        "tasks": combined,
        "review_complete": False,
        "success_criteria": review.success_criteria or state.get("success_criteria", []),
    }


def route_after_review(state):
    return "aggregate" if state.get("review_complete", True) else "execute"


async def aggregate(state):
    run = state_run(state)
    results = [AgentResult(**item) for item in state.get("results", [])]
    provider_unavailable = any(
        "AI_PROVIDER_UNAVAILABLE" in [*item.reason_codes, *item.warnings]
        for item in results
    )
    if provider_unavailable:
        proposal = SupervisorProposal(
            summary=" ".join(item.summary for item in results),
            evidence_refs=list(
                dict.fromkeys(reference for item in results for reference in item.evidence_refs)
            ),
            actions=[action for item in results for action in item.proposals],
            warnings=list(dict.fromkeys(warning for item in results for warning in item.warnings)),
            success_criteria_met=state.get("success_criteria", [])
            if all(item.status == AgentTaskStatus.COMPLETED for item in results)
            else [],
        )
    else:
        prompt = aggregate_prompt(
            run.objective,
            state.get("success_criteria", []),
            [item.model_dump(mode="json") for item in results],
        )
        try:
            proposal = await structured(
                prompt,
                SupervisorProposal,
                max_tokens=1200,
                timeout_seconds=limits.task_timeout_seconds,
            )
        except Exception:
            proposal = SupervisorProposal(
                summary=" ".join(item.summary for item in results),
                evidence_refs=list(
                    dict.fromkeys(
                        reference for item in results for reference in item.evidence_refs
                    )
                ),
                actions=[action for item in results for action in item.proposals],
                warnings=list(
                    dict.fromkeys(warning for item in results for warning in item.warnings)
                ),
                success_criteria_met=state.get("success_criteria", [])
                if all(item.status == AgentTaskStatus.COMPLETED for item in results)
                else [],
            )
    tasks = {item["task_id"]: AgentTask(**item) for item in state.get("tasks", [])}
    pending_actions = []
    if run.approval_status != AgentApprovalStatus.REJECTED:
        for result in results:
            task = tasks.get(result.task_id)
            if not task:
                continue
            planned_calls = {item.tool_name: item for item in task.tool_calls}
            for action in result.proposals:
                tool_name = action.get("tool_name")
                policy = policies().get(tool_name)
                planned = planned_calls.get(tool_name)
                if not policy or not policy.requires_approval or not planned:
                    continue
                pending_actions.append(
                    {
                        "task_id": task.task_id,
                        "tool_name": tool_name,
                        "arguments": planned.arguments,
                    }
                )
    proposal.actions = pending_actions
    proposal.summary = normalize_narrative(proposal.summary)
    proposal.warnings = normalize_narratives(proposal.warnings)
    proposal.evidence_refs = [
        reference for reference in proposal.evidence_refs if reference in run.evidence_refs
    ]
    if not proposal.evidence_refs:
        proposal.evidence_refs = list(run.evidence_refs)
    run.proposal = proposal.model_dump(mode="json")
    run.evidence_refs = list(dict.fromkeys([*run.evidence_refs, *proposal.evidence_refs]))
    run.status = (
        AgentRunStatus.APPROVAL_REQUIRED if pending_actions else AgentRunStatus.VERIFYING
    )
    run.current_step += 1
    return {"run": run.model_dump(mode="python")}


def route_after_aggregate(state):
    return (
        "end"
        if state_run(state).status == AgentRunStatus.APPROVAL_REQUIRED
        else "verify"
    )


async def apply(state):
    run = state_run(state)
    tasks = {item["task_id"]: AgentTask(**item) for item in state.get("tasks", [])}
    applied = []
    run.status = AgentRunStatus.APPLYING
    for action in (run.proposal or {}).get("actions", []):
        task = tasks.get(action.get("task_id"))
        if not task:
            applied.append(
                {"status": ToolExecutionStatus.FAILED, "reason_code": "TASK_NOT_FOUND"}
            )
            continue
        result = await invoke_tool(
            task,
            action.get("tool_name", ""),
            action.get("arguments", {}),
            run.permissions,
            state["token"],
            AgentApprovalStatus.APPROVED,
        )
        if result.get("status") == ToolExecutionStatus.COMPLETED:
            result["verification"] = await verify_application(
                task,
                action.get("tool_name", ""),
                action.get("arguments", {}),
                result,
                state["token"],
            )
        applied.append(result)
    run.proposal = {**(run.proposal or {}), "applied_results": applied}
    run.status = AgentRunStatus.VERIFYING
    run.current_step += 1
    return {"run": run.model_dump(mode="python")}


async def verify(state):
    run = state_run(state)
    results = [AgentResult(**item) for item in state.get("results", [])]
    applied = (run.proposal or {}).get("applied_results", [])
    actions = (run.proposal or {}).get("actions", [])
    rejected = run.approval_status == AgentApprovalStatus.REJECTED
    result_ok = bool(results) and all(
        item.status in {AgentTaskStatus.COMPLETED, AgentTaskStatus.INSUFFICIENT_EVIDENCE}
        for item in results
    )
    completed_claims = any(item.status == AgentTaskStatus.COMPLETED for item in results)
    proposal_refs = set((run.proposal or {}).get("evidence_refs", []))
    result_refs = {
        reference
        for item in results
        for reference in item.evidence_refs
    }
    claims_grounded = all(
        item.status != AgentTaskStatus.COMPLETED
        or bool(item.evidence_refs)
        and set(item.evidence_refs).issubset(set(run.evidence_refs))
        for item in results
    )
    evidence_ok = (
        (not completed_claims or bool(run.evidence_refs))
        and proposal_refs.issubset(set(run.evidence_refs))
        and result_refs.issubset(set(run.evidence_refs))
        and claims_grounded
    )
    project_scope_ok = all(
        item.get("project_id") == run.project_id for item in run.completed_tasks
    )
    apply_ok = not applied or all(
        item.get("status") == ToolExecutionStatus.COMPLETED
        and item.get("verification", {}).get("status") == ToolExecutionStatus.COMPLETED
        for item in applied
    )
    apply_count_ok = (
        not actions
        or rejected
        or (run.approval_status == AgentApprovalStatus.APPROVED and len(applied) == len(actions))
    )
    verified = result_ok and evidence_ok and project_scope_ok and apply_ok and apply_count_ok
    verification = {
        "verified": verified,
        "project_id": run.project_id,
        "evidence_refs_resolved": evidence_ok,
        "completed_claims_grounded": claims_grounded,
        "project_scope_valid": project_scope_ok,
        "approval_status": run.approval_status,
        "applied_count": len(applied),
        "expected_apply_count": len(actions),
        "apply_count_valid": apply_count_ok,
        "rejected": rejected,
    }
    run.proposal = {**(run.proposal or {}), "verification": verification}
    reason_codes = {
        code for item in results for code in [*item.reason_codes, *item.warnings]
    }
    if "AI_PROVIDER_UNAVAILABLE" in reason_codes:
        run.status = AgentRunStatus.FAILED
        run.error_code = "AI_PROVIDER_UNAVAILABLE"
    elif verified:
        run.status = AgentRunStatus.COMPLETED
        run.error_code = None
    else:
        run.status = AgentRunStatus.FAILED
        run.error_code = (
            "VALIDATION_FAILED"
            if "VALIDATION_FAILED" in reason_codes
            else "VERIFICATION_FAILED"
        )
    run.current_step += 1
    return {"run": run.model_dump(mode="python")}
