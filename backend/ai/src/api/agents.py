import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.runnables import RunnableConfig

from src.agents.supervisor.graph import canonical_workflow
from src.agents.supervisor.policy import routing_policies
from src.core.dependency import get_current_user, oauth2_scheme
from src.core.infrastructure.configuration import settings
from src.memory.project_memory import project_memory
from src.memory.short_term import run_store
from src.runtime.limits import limits
from src.runtime.models import AgentRunRequest, VeriqRunState
from src.schemas.auth import CurrentUser
from src.services.agent_metrics import agentops
from src.services.token_accounting import current_usage, start_accounting
from src.tools.testing import get_project_context


router = APIRouter(prefix="/tac-tu", tags=["Tác tử kiểm thử"])


async def project_access(project_id, token):
    config = RunnableConfig(configurable={"token": f"Bearer {token}", "project_id": project_id})
    raw = await get_project_context.ainvoke({"project_id": project_id}, config=config)
    try:
        context = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=502, detail={"code": "PROJECT_CONTEXT_INVALID"}) from error
    project = context.get("project") or {}
    membership = project.get("current_membership") or {}
    permissions = project.get("current_permissions") or []
    if not project.get("_id") or not membership.get("project_role"):
        raise HTTPException(status_code=403, detail={"code": "PROJECT_ACCESS_DENIED"})
    return membership["project_role"], permissions


@router.post("/luot-chay", status_code=201)
async def create_agent_run(
    payload: AgentRunRequest,
    token: str = Depends(oauth2_scheme),
    user: CurrentUser = Depends(get_current_user),
):
    if payload.intent and payload.intent not in routing_policies():
        raise HTTPException(status_code=422, detail={"code": "AGENT_INTENT_INVALID"})
    role, permissions = await project_access(payload.project_id, token)
    run = VeriqRunState(
        project_id=payload.project_id,
        user_id=user.id,
        role=role,
        permissions=permissions,
        objective=payload.objective,
        intent=payload.intent,
        model_metadata={"provider": "huggingface", "model": settings.LLM_MODEL},
    )
    start_accounting()
    agentops.record_session_start(run.run_id, user.id)
    try:
        result = await asyncio.wait_for(
            canonical_workflow.ainvoke(
                {
                    "run": run.model_dump(mode="python"),
                    "token": f"Bearer {token}",
                    "evidence": [item.model_dump(mode="python") for item in payload.evidence],
                    "target_artifact_ids": payload.target_artifact_ids,
                    "constraints": payload.constraints,
                    "tasks": [],
                    "results": [],
                }
            ),
            timeout=limits.run_timeout_seconds,
        )
    except TimeoutError:
        run.status = "FAILED"
        run.error_code = "AGENT_LIMIT_REACHED"
        run.observations.append({"phase": "RUN", "reason_code": "AGENT_LIMIT_REACHED"})
        run.token_usage = current_usage()
        await run_store.save(run)
        agentops.record_session_end(run.run_id, "failed")
        return run
    completed = VeriqRunState(**result["run"])
    completed.token_usage = current_usage()
    await run_store.save(completed)
    if completed.status == "COMPLETED":
        await project_memory.record_verified(completed)
    agentops.record_session_end(
        completed.run_id,
        "done" if completed.status in {"COMPLETED", "APPROVAL_REQUIRED"} else "failed",
    )
    return completed


@router.get("/luot-chay/{run_id}")
async def get_agent_run(
    run_id: str,
    token: str = Depends(oauth2_scheme),
    user: CurrentUser = Depends(get_current_user),
):
    run = await run_store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    if run.user_id != user.id and user.system_role.value != "ADMIN":
        _, permissions = await project_access(run.project_id, token)
        if "proposal.read" not in permissions:
            raise HTTPException(status_code=403, detail={"code": "PROJECT_ACCESS_DENIED"})
    return run
