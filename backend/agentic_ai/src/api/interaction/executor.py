import json
from datetime import datetime, timezone
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger

from src.core.logging_route import LoggingRoute
from src.agents.routing import semantic_router
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.registry import PromptType, registry
from src.harness.agentops import agentops
from src.harness.context import context
from src.harness.orchestration import orchestration
from src.harness.security import security
from src.schemas.interaction import ChatRequest
from src.core.dependency import CurrentUser, get_current_user
from src.workflow.orchestration import supervisor
from src.services.workspace import workspace
from src.services.token_accounting import current_usage, start_accounting

router = APIRouter(route_class=LoggingRoute)


async def get_tier_routed_user(
    current_user: CurrentUser = Depends(get_current_user),
):
    """Keep model routing bound to this request, including streaming responses."""
    from src.utils.huggingface import reset_request_ai_tier, set_request_ai_tier

    token = set_request_ai_tier(current_user.ai_tier.value)
    try:
        yield current_user
    finally:
        reset_request_ai_tier(token)

def require_mode_tier(mode: str, tier: str, role: str = "") -> None:
    if (
        mode != "chat"
        and str(role).lower() != "admin"
        and str(tier).upper() not in {"PRO", "PREMIUM"}
    ):
        raise HTTPException(status_code=403, detail={"code": "advanced_mode_requires_pro"})

def _validate_audio(req: ChatRequest) -> None:
    if not req.audio_data:
        return
    from src.utils.multimodal import validate_audio
    validate_audio(req.audio_data)

def _validate_image(req: ChatRequest) -> None:
    if not req.image_data:
        return
    from src.utils.multimodal import validate_image
    validate_image(req.image_data)

async def _persist_conversation_turns(
    session_id: str,
    user_id: str,
    user_content: str,
    assistant_content: str,
    attachments: list[dict],
) -> None:
    if not session_id or not assistant_content:
        return
    await context.save_turn(session_id, "user", user_content)
    await context.save_turn(session_id, "assistant", assistant_content)
    try:
        from src.memory.management import memory_manager
        from src.services.history import HistoryService
        from src.utils.background import create_background_task

        user_message = {"user_id": user_id, "role": "user", "content": user_content}
        if attachments:
            user_message["attachments"] = attachments
        await HistoryService.add_message(session_id, user_message)
        await HistoryService.add_message(
            session_id,
            {"user_id": user_id, "role": "assistant", "content": assistant_content},
        )
        create_background_task(
            memory_manager.add_memory(
                [
                    {"role": "user", "content": user_content},
                    {"role": "assistant", "content": assistant_content},
                ],
                user_id,
            ),
            f"chat-memory-{session_id}",
        )
        create_background_task(
            HistoryService.generate_title(
                session_id,
                user_id,
                user_content,
                assistant_content,
            ),
            f"chat-title-{session_id}",
        )
    except Exception:
        logger.exception("Chat history persistence to database error")

async def _reserve_upload_quota(req: ChatRequest):
    item_type = None
    if req.folder_data:
        item_type = "folder"
    elif req.file_data:
        item_type = "document"
    if item_type is None:
        return True, None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                f"{settings.USAGE_URL}/han-muc/tai-len/dat-cho",
                json={"item_type": item_type},
                headers={"Authorization": f"Bearer {req.token}"},
            )
            if res.status_code == 200:
                return True, None
            if res.status_code in {403, 429}:
                return False, "upload_quota_exceeded"
    except Exception:
        logger.exception("Quota reservation request error")
    return True, None

async def _reserve_ai_quota(req: ChatRequest):
    if req.role == "admin" or req.ai_tier in ["PRO", "PREMIUM"]:
        return True, None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                f"{settings.USAGE_URL}/han-muc/xac-minh",
                params={
                    "user_id": req.user_id,
                    "role": req.role,
                    "ai_tier": req.ai_tier,
                    "feature": req.mode,
                },
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
            if res.status_code == 200:
                return True, None
            if res.status_code == 429:
                return False, "ai_quota_exceeded"
    except Exception:
        logger.exception("AI quota reservation request error")
    return True, None

async def _consume_ai_quota(req: ChatRequest, query: str, answer: str, usage: dict):
    if not req.user_id:
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{settings.USAGE_URL}/han-muc/su-dung",
                json={
                    "user_id": req.user_id,
                    "feature": req.mode,
                    "role": req.role,
                    "ai_tier": req.ai_tier,
                    "input_tokens": usage.get("query_tokens", len(query.split())),
                    "output_tokens": usage.get("answer_tokens", len(answer.split())),
                },
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
    except Exception:
        logger.exception("AI quota consumption request error")

@router.post("")
async def chat_endpoint(
    req: ChatRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_tier_routed_user),
):
    req.user_id = str(current_user.id)
    req.role = current_user.role.value
    req.ai_tier = current_user.ai_tier.value
    require_mode_tier(req.mode, req.ai_tier, req.role)
    logger.info("Chat request started query_chars={}", len(req.query))
    token = request.headers.get("Authorization")
    if token:
        req.token = token.replace("Bearer ", "")

    is_quota_ok, quota_code = await _reserve_upload_quota(req)
    if not is_quota_ok:
        return {"answer": "", "route": "error", "error_code": quota_code}

    try:
        _validate_image(req)
        _validate_audio(req)
    except (ValueError, RuntimeError):
        return {"answer": "", "route": "error", "error_code": "multimodal_processing_failed"}

    scan = await security.ascan_input(req.query, user_id=req.user_id or "")
    if not scan.passed:
        logger.warning("Query execution blocked due to security policy violation")
        return {"answer": "", "route": "blocked", "error_code": "input_security_blocked"}

    original_query = scan.sanitized_text
    req.query = original_query
    await workspace.start(
        req.session_id or "", req.user_id, req.mode, original_query, req.approval_policy
    )
    mode_directive = await workspace.mode_context(req.session_id or "", req.user_id, req.mode)
    execution_data = {**req.model_dump(), "mode_directive": mode_directive}

    try:
        quota_ok, quota_code = await _reserve_ai_quota(req)
        if not quota_ok:
            return {"answer": "", "route": "error", "error_code": quota_code}
        start_accounting()
        ctx = await context.build_context(
            session_id=req.session_id or "",
            user_id=req.user_id,
            query=req.query,
            document_ids=req.document_ids,
        )
        req.conversation_history = ctx.chat_history
        execution_data = {
            **req.model_dump(),
            "mode_directive": mode_directive,
            "user_preferences": ctx.user_preferences,
        }
        if req.document_ids:
            from src.tools.http_client import (
                INTERNAL_API_URL,
                make_api_request as _make_api_request,
            )

            for doc_id in req.document_ids:
                try:
                    doc_res = await _make_api_request(
                        "GET",
                        f"{INTERNAL_API_URL}/tai-lieu/{doc_id}",
                        headers={"Authorization": f"Bearer {req.token}"},
                        timeout=10.0,
                    )
                    if doc_res.status_code not in [200, 201]:
                        logger.warning(f"Document {doc_id} access denied or not found")
                        return {
                            "answer": "",
                            "route": "error",
                            "error_code": "document_access_denied",
                        }
                except Exception:
                    logger.exception(f"Document {doc_id} access verification error")
                    return {
                        "answer": "",
                        "route": "error",
                        "error_code": "document_access_verification_failed",
                    }

        route_data = {}
        if req.mode == "plan":
            route = "plan"
        elif req.mode in {"work", "goal"} or req.thinking:
            route = "supervisor"
        elif req.mode == "learn":
            route = "knowledge"
        elif req.document_ids or req.file_data or req.folder_data:
            route = "knowledge"
        elif req.mode == "chat" and not req.useWeb:
            # Avoid an unnecessary model round-trip for ordinary conversation.
            route = "chat"
        else:
            route_data = await semantic_router.execute(req.query)
            route = route_data.get("route", "knowledge")

        final_answer = ""

        if route == "plan":
            from src.agents.planning import planner

            steps = await planner.create_plan({**execution_data, "dry_run": True})
            await workspace.save_plan(req.session_id or "", req.user_id, steps)
            final_answer = "\n".join(
                f"{index + 1} {step.get('task', '')}" for index, step in enumerate(steps)
            )
        elif route == "chat":
            final_answer = route_data.get("answer", "")
            if not final_answer:
                from langchain_core.messages import HumanMessage
                from src.utils.huggingface import create_chat_model

                chat_llm = create_chat_model()

                text_prompt = registry.get(PromptType.CHAT_ASSISTANT).format(query=req.query)
                if req.image_data:
                    content = [
                        {"type": "text", "text": text_prompt},
                        {"type": "image_url", "image_url": {"url": req.image_data}},
                    ]
                else:
                    content = text_prompt

                if req.audio_data:
                    if isinstance(content, str):
                        content = [{"type": "text", "text": content}]
                    content.append(
                        {"type": "audio_url", "audio_url": {"url": req.audio_data}}
                    )

                res = await chat_llm.ainvoke([HumanMessage(content=content)], max_tokens=256)
                final_answer = res.content
        elif route == "knowledge":
            from src.agents.analysis import researcher

            final_answer = await researcher.execute(execution_data)
        else:
            async for event in supervisor.execute_plan(execution_data):
                if event["type"] == "message":
                    final_answer += event.get("chunk", "")
                elif event["type"] == "plan":
                    await workspace.save_plan(
                        req.session_id or "", req.user_id, event.get("steps", []), status="running"
                    )
                elif event["type"] == "tool_result":
                    await workspace.update_steps(
                        req.session_id or "", req.user_id, event.get("task_status", {})
                    )

        final_answer = await security.ascan_output(final_answer)
        await _consume_ai_quota(req, original_query, final_answer, current_usage())
        await _persist_conversation_turns(
            req.session_id or "",
            req.user_id,
            original_query,
            final_answer,
            req.attachments,
        )
        await workspace.finish(req.session_id or "", req.user_id, req.mode, bool(final_answer))
        return {
            "answer": final_answer,
            "route": "agentic_ai",
            "error_code": None if final_answer else "empty_model_response",
        }
    except Exception:
        logger.exception("AI agent workflow execution error")
        return {"answer": "", "route": "error", "error_code": "agent_workflow_failed"}
