import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
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
from src.services.token_accounting import start_accounting
from src.api.interaction.executor import (
    _validate_audio,
    _validate_image,
    _persist_conversation_turns,
)

router = APIRouter(route_class=LoggingRoute)


def _sanitize_stream_piece(piece: str) -> str:
    """Apply deterministic output protection without stripping token whitespace."""
    if piece and not piece.strip():
        return piece
    from src.core.security.guardrails import guardrails_engine

    assessment = guardrails_engine.inspect_output(piece)
    if assessment.get("threat_category") == "credential_leak":
        raise PermissionError("output_credential_leak_blocked")
    return str(assessment.get("sanitized_text", piece))


@router.get("/kha-nang")
async def chat_capabilities(
    current_user: CurrentUser = Depends(get_current_user),
):
    """Return model and interaction capabilities for the authenticated user."""
    return {
        "model": settings.LLM_MODEL,
        "audio_input": True,
        "code_execution": True,
        "mcp": True,
    }

@router.post("/phat-truc-tiep")
async def chat_stream_endpoint(
    req: ChatRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Stream one authenticated assistant interaction as server-sent events."""
    session_id = req.session_id or ""
    user_id = str(current_user.id)
    req.user_id = user_id
    req.role = current_user.role.value

    token = request.headers.get("Authorization")
    if token:
        req.token = token.replace("Bearer ", "")

    async def response_generator():
        yield "event: start\ndata: {}\n\n"
        try:
            _validate_image(req)
            _validate_audio(req)
        except (ValueError, RuntimeError):
            yield f"event: error\ndata: {json.dumps({'code': 'multimodal_processing_failed'})}\n\n"
            yield "event: done\ndata: [DONE]\n\n"
            return

        scan = await security.ascan_input(
            req.query,
            session_id=session_id,
            user_id=user_id,
        )
        if not scan.passed:
            agentops.record_security_event(
                session_id,
                "prompt_injection_blocked",
                scan.risk_score,
                scan.violations,
            )
            yield f"event: error\ndata: {json.dumps({'code': 'input_security_blocked'})}\n\n"
            yield "event: done\ndata: [DONE]\n\n"
            return

        if scan.violations:
            agentops.record_security_event(
                session_id,
                "pii_redacted",
                scan.risk_score,
                scan.violations,
            )

        original_query = scan.sanitized_text
        req.query = original_query
        agentops.record_session_start(session_id, user_id, original_query)
        await workspace.start(session_id, user_id, req.mode, original_query, req.approval_policy)
        mode_directive = await workspace.mode_context(session_id, user_id, req.mode)

        try:
            start_accounting()

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
                            yield f"event: error\ndata: {json.dumps({'code': 'document_access_denied'})}\n\n"
                            agentops.record_session_end(session_id, "failed")
                            yield "event: done\ndata: [DONE]\n\n"
                            return
                    except Exception:
                        logger.exception(f"Document {doc_id} access verification error")
                        yield f"event: error\ndata: {json.dumps({'code': 'document_access_verification_failed'})}\n\n"
                        agentops.record_session_end(session_id, "failed")
                        yield "event: done\ndata: [DONE]\n\n"
                        return

            ctx = await context.build_context(
                session_id=session_id,
                user_id=user_id,
                query=req.query,
                document_ids=req.document_ids,
            )
            req.conversation_history = ctx.chat_history
            execution_data = {
                **req.model_dump(),
                "mode_directive": mode_directive,
                "user_preferences": ctx.user_preferences,
            }

            route_data = {}
            if req.mode == "plan":
                route = "plan"
            elif req.mode in {"work", "goal"}:
                route = "supervisor"
            elif req.mode == "learn":
                route = "knowledge"
            elif req.document_ids or req.file_data or req.folder_data:
                route = "knowledge"
            elif req.mode == "chat" and not req.useWeb:
                route = "chat"
            else:
                route_data = await semantic_router.execute(req.query)
                route = route_data.get("route", "knowledge")

            final_answer = ""

            if route == "plan":
                from src.agents.planning import planner

                steps = await planner.create_plan({**execution_data, "dry_run": True})
                await workspace.save_plan(session_id, user_id, steps)
                final_answer = "\n".join(
                    f"{index + 1} {step.get('task', '')}" for index, step in enumerate(steps)
                )
                yield "event: plan\ndata: " + json.dumps({"steps": steps}) + "\n\n"
                yield "event: message\ndata: " + json.dumps({"chunk": final_answer}) + "\n\n"
            elif route == "chat":
                fast_answer = route_data.get("answer", "")
                if fast_answer:
                    yield f"event: message\ndata: {json.dumps({'chunk': fast_answer})}\n\n"
                    final_answer = fast_answer
                else:
                    from langchain_core.messages import HumanMessage
                    from src.utils.huggingface import create_chat_model

                    chat_llm = create_chat_model()

                    text_prompt = registry.get_base(PromptType.CHAT_ASSISTANT).format(
                        query=req.query
                    )
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

                    try:
                        active_model = settings.LLM_MODEL
                        yield "event: model\ndata: " + json.dumps(
                            {
                                "model": active_model,
                                "audio_input": True,
                            }
                        ) + "\n\n"
                        raw_answer = ""
                        async for chunk in chat_llm.astream(
                            [HumanMessage(content=content)], max_tokens=128
                        ):
                            piece = str(chunk.content or "")
                            if not piece:
                                continue
                            safe_piece = _sanitize_stream_piece(piece)
                            if not safe_piece:
                                continue
                            raw_answer += safe_piece
                            yield (
                                "event: message\ndata: "
                                + json.dumps({"chunk": safe_piece})
                                + "\n\n"
                            )
                        final_answer = await security.ascan_output(raw_answer)
                    except RuntimeError:
                        logger.exception("Runtime error during LLM chat stream")
                        yield (
                            "event: error\ndata: "
                            + json.dumps({"code": "model_generation_failed"})
                            + "\n\n"
                        )
                    except Exception:
                        logger.exception("Unexpected error during LLM chat stream")

            elif route == "knowledge":
                from src.agents.analysis import researcher

                final_answer = await researcher.execute(execution_data)
                yield "event: message\ndata: " + json.dumps({"chunk": final_answer}) + "\n\n"

            else:
                import asyncio

                heartbeat_queue: asyncio.Queue = asyncio.Queue()

                async def heartbeat_sender():
                    while True:
                        await asyncio.sleep(10)
                        await heartbeat_queue.put({"type": "heartbeat"})

                hb_task = asyncio.create_task(heartbeat_sender())

                async def drain_supervisor():
                    try:
                        req_dict = execution_data.copy()

                        from src.agents.planning import planner

                        async for chunk in planner.stream_plan(req_dict):
                            if chunk["type"] == "plan":
                                req_dict["plan"] = chunk["nodes"]
                                await workspace.save_plan(
                                    session_id, user_id, chunk["nodes"], status="running"
                                )
                                await heartbeat_queue.put({"type": "plan", "steps": chunk["nodes"]})
                            elif chunk["type"] == "error":
                                await heartbeat_queue.put(chunk)
                                return

                        async for event in orchestration.run(
                            supervisor.execute_plan, req_dict, session_id
                        ):
                            await heartbeat_queue.put(event)
                    except Exception:
                        logger.exception("Error in drain_supervisor")
                        await heartbeat_queue.put({"type": "error", "code": "orchestration_failed"})
                    finally:
                        await heartbeat_queue.put({"type": "__done__"})

                exec_task = asyncio.create_task(drain_supervisor())

                try:
                    while True:
                        event = await heartbeat_queue.get()
                        event_type = event["type"]

                        if event_type == "__done__":
                            break
                        elif event_type == "heartbeat":
                            yield "event: heartbeat\ndata: {}\n\n"
                        elif event_type == "status":
                            yield f"event: status\ndata: {json.dumps({'code': event.get('code', 'processing')})}\n\n"
                        elif event_type == "plan":
                            task_status = event.get("task_status", {})
                            normalized_status = {
                                str(key): value for key, value in task_status.items()
                            }
                            await workspace.update_steps(session_id, user_id, task_status)
                            public_steps = [
                                {
                                    "id": str(step.get("id", index + 1)),
                                    "index": index + 1,
                                    "status": normalized_status.get(
                                        str(step.get("id", index + 1)), "pending"
                                    ),
                                    "task": str(step.get("task", "")),
                                }
                                for index, step in enumerate(event.get("steps", []))
                            ]
                            yield f"event: plan\ndata: {json.dumps({'steps': public_steps})}\n\n"
                        elif event_type == "tool_result":
                            await workspace.update_steps(
                                session_id, user_id, event.get("task_status", {})
                            )
                            agentops.record_tool_call(
                                session_id,
                                event.get("agent", "unknown"),
                                duration_ms=0,
                                success=True,
                            )
                            agent_name = event.get("agent", "unknown")
                            yield f"event: tool\ndata: {json.dumps({'agent': agent_name, 'status': 'completed', 'task_status': event.get('task_status', {})})}\n\n"
                        elif event_type == "message":
                            message_chunk = str(event.get("chunk", ""))
                            final_answer += message_chunk
                            yield f"event: message\ndata: {json.dumps({'chunk': message_chunk})}\n\n"
                        elif event_type == "error":
                            yield f"event: error\ndata: {json.dumps({'code': event.get('code', 'execution_failed')})}\n\n"
                finally:
                    hb_task.cancel()
                    exec_task.cancel()
                    import asyncio

                    await asyncio.gather(hb_task, exec_task, return_exceptions=True)

            if final_answer:
                final_answer = await security.ascan_output(final_answer, session_id=session_id)

            await _persist_conversation_turns(
                session_id,
                user_id,
                original_query,
                final_answer,
                req.attachments,
            )

            await workspace.finish(session_id, user_id, req.mode, bool(final_answer))
            agentops.record_session_end(session_id, "done")

        except Exception:
            logger.exception("Chat stream execution unexpected error")
            await workspace.finish(session_id, user_id, req.mode, False)
            agentops.record_session_end(session_id, "failed")
            yield f"event: error\ndata: {json.dumps({'code': 'chat_stream_failed'})}\n\n"

        yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(response_generator(), media_type="text/event-stream")
