import json
from datetime import datetime, timezone

import httpx
from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from loguru import logger
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
from src.schemas.auth import Role, Tier
from src.workflow.orchestration import supervisor

router = APIRouter(route_class=LoggingRoute, prefix="/tro-chuyen")

@router.post("")
async def chat_endpoint(
    req: ChatRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
):
    req.user_id = str(current_user.id)
    logger.info("Chat request started query_chars={}", len(req.query))
    token = request.headers.get("Authorization")
    if token:
        req.token = token.replace("Bearer ", "")

    scan = await security.ascan_input(req.query, user_id=req.user_id or "")
    if not scan.passed:
        logger.warning("Query execution blocked due to security policy violation")
        return {
            "answer": "",
            "route": "blocked",
            "error_code": "input_security_blocked",
        }

    req.query = scan.sanitized_text

    try:
        if req.document_ids:
            from src.tools.http_client import INTERNAL_API_URL, make_api_request as _make_api_request

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
        if req.thinking:
            route = "supervisor"
        elif req.document_ids or req.file_data or req.folder_data:
            route = "knowledge"
        else:
            route_data = await semantic_router.execute(req.query)
            route = route_data.get("route", "knowledge")
            
        final_answer = ""

        if route == "chat":
            final_answer = route_data.get("answer", "")
            if not final_answer:
                from huggingface_hub import AsyncInferenceClient
                from langchain_core.messages import HumanMessage
                from src.utils.huggingface import HFInferenceChat

                from src.core.infrastructure.configuration import settings

                llama_client = AsyncInferenceClient(
                    model=settings.LLM_MODEL, token=settings.HF_TOKEN
                )
                chat_llm = HFInferenceChat(
                    client=llama_client, model=settings.LLM_MODEL
                )

                text_prompt = registry.get(PromptType.CHAT_ASSISTANT).format(
                    query=req.query
                )
                if req.image_data:
                    content = [
                        {"type": "text", "text": text_prompt},
                        {"type": "image_url", "image_url": {"url": req.image_data}},
                    ]
                else:
                    content = text_prompt

                res = await chat_llm.ainvoke(
                    [HumanMessage(content=content)], max_tokens=256
                )
                final_answer = res.content
        elif route == "knowledge":
            from src.agents.analysis import researcher
            final_answer = await researcher.execute(req.model_dump())
        else:
            async for event in supervisor.execute_plan(req.model_dump()):
                if event["type"] == "message":
                    final_answer += event.get("chunk", "")

        final_answer = await security.ascan_output(final_answer)
        return {
            "answer": final_answer,
            "route": "agentic_ai",
            "error_code": None if final_answer else "empty_model_response",
        }
    except Exception:
        logger.exception("AI agent workflow execution error")
        return {
            "answer": "",
            "route": "error",
            "error_code": "agent_workflow_failed",
        }

async def _check_upload_quota(req: ChatRequest):
    item_type = None
    if req.folder_data:
        item_type = "folder"
    elif req.file_data:
        item_type = "document"
    elif req.image_data:
        item_type = "image"
        
    if not item_type:
        return True, None
        
    try:
        from src.core.infrastructure.database import database
        user = await database.mongodb[settings.AGENTIC_AI_DB_NAME].users.find_one({"_id": req.user_id})
        ai_tier = user.get("ai_tier", Tier.BASIC.value) if user else Tier.BASIC.value
        is_admin = user.get("role") == Role.ADMIN.value if user else False
        
        if is_admin or ai_tier != Tier.BASIC.value:
            return True, None

        async with httpx.AsyncClient(timeout=10.0) as c:
            resp = await c.get(
                f"{settings.USAGE_URL}/han-muc/tai-len/xac-minh",
                params={"item_type": item_type},
                headers={"Authorization": f"Bearer {req.token}"} if req.token else {}
            )
            if resp.status_code != 200:
                return False, "upload_quota_exceeded"
            return True, None
    except Exception:
        logger.exception("Upload quota verification error")
        return False, "upload_quota_verification_failed"

async def _consume_upload_quota(req: ChatRequest):
    item_type = None
    if req.folder_data:
        item_type = "folder"
    elif req.file_data:
        item_type = "document"
    elif req.image_data:
        item_type = "image"
        
    if not item_type:
        return
        
    try:
        from src.core.infrastructure.database import database
        user = await database.mongodb[settings.AGENTIC_AI_DB_NAME].users.find_one({"_id": req.user_id})
        ai_tier = user.get("ai_tier", Tier.BASIC.value) if user else Tier.BASIC.value
        is_admin = user.get("role") == Role.ADMIN.value if user else False
        
        if is_admin or ai_tier != Tier.BASIC.value:
            return

        async with httpx.AsyncClient(timeout=10.0) as c:
            await c.post(
                f"{settings.USAGE_URL}/han-muc/tai-len/tieu-thu",
                json={"user_id": req.user_id, "item_type": item_type, "req_reset_hours": 24},
                headers={"Authorization": f"Bearer {req.token}"} if req.token else {}
            )
    except Exception:
        logger.exception("Upload quota consumption error")

@router.post("/phat-truc-tiep")
async def stream_endpoint(
    req: ChatRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
):
    req.user_id = str(current_user.id)
    logger.info("Chat stream started query_chars={}", len(req.query))
    token = request.headers.get("Authorization")
    bearer_token = token.replace("Bearer ", "") if token else None

    async def response_generator():
        if bearer_token:
            req.token = bearer_token

        session_id = req.session_id or ""
        user_id = req.user_id or ""

        scan = await security.ascan_input(req.query, session_id=session_id, user_id=user_id)
        if not scan.passed:
            agentops.record_security_event(
                session_id, "prompt_injection_blocked", scan.risk_score, scan.violations
            )
            yield f"event: error\ndata: {json.dumps({'code': 'input_security_blocked'})}\n\n"
            yield "event: done\ndata: [DONE]\n\n"
            return

        if scan.violations:
            agentops.record_security_event(
                session_id, "pii_redacted", scan.risk_score, scan.violations
            )

        req.query = scan.sanitized_text

        agentops.record_session_start(session_id, user_id, req.query)

        try:
            is_quota_ok, quota_code = await _check_upload_quota(req)
            if not is_quota_ok:
                yield f"event: error\ndata: {json.dumps({'code': quota_code})}\n\n"
                yield "event: done\ndata: [DONE]\n\n"
                agentops.record_session_end(session_id, "failed")
                return

            if req.document_ids:
                from src.tools.http_client import INTERNAL_API_URL, make_api_request as _make_api_request

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
                            return
                    except Exception:
                        logger.exception(f"Document {doc_id} access verification error")
                        yield f"event: error\ndata: {json.dumps({'code': 'document_access_verification_failed'})}\n\n"
                        agentops.record_session_end(session_id, "failed")
                        return

            ctx = await context.build_context(
                session_id=session_id,
                user_id=user_id,
                query=req.query,
                document_ids=req.document_ids,
            )
            req.conversation_history = ctx.chat_history

            route_data = {}
            if req.thinking:
                route = "supervisor"
            elif req.document_ids or req.file_data or req.folder_data:
                route = "knowledge"
            else:
                route_data = await semantic_router.execute(req.query)
                route = route_data.get("route", "knowledge")
                
            final_answer = ""

            if route == "chat":
                fast_answer = route_data.get("answer", "")
                if fast_answer:
                    yield f"event: message\ndata: {json.dumps({'chunk': fast_answer})}\n\n"
                    final_answer = fast_answer
                else:
                    from huggingface_hub import AsyncInferenceClient
                    from langchain_core.messages import HumanMessage
                    from src.utils.huggingface import HFInferenceChat

                    from src.core.infrastructure.configuration import settings

                    llama_client = AsyncInferenceClient(
                        model=settings.LLM_MODEL, token=settings.HF_TOKEN
                    )
                    chat_llm = HFInferenceChat(
                        client=llama_client, model=settings.LLM_MODEL
                    )

                    text_prompt = registry.get(PromptType.CHAT_ASSISTANT).format(
                        query=req.query
                    )
                    if req.image_data:
                        content = [
                            {"type": "text", "text": text_prompt},
                            {"type": "image_url", "image_url": {"url": req.image_data}},
                        ]
                    else:
                        content = text_prompt

                    try:
                        response = await chat_llm.ainvoke(
                            [HumanMessage(content=content)], max_tokens=256
                        )
                        final_answer = await security.ascan_output(response.content)
                        if final_answer:
                            yield "event: message\ndata: " + json.dumps(
                                {"chunk": final_answer}
                            ) + "\n\n"
                    except RuntimeError:
                        logger.exception("Runtime error during LLM chat stream")
                        yield "event: error\ndata: " + json.dumps(
                            {"code": "model_generation_failed"}
                        ) + "\n\n"
                    except Exception:
                        logger.exception("Unexpected error during LLM chat stream")

            elif route == "knowledge":
                from src.agents.analysis import researcher
                final_answer = await researcher.execute(req.model_dump())
                yield "event: message\ndata: " + json.dumps(
                    {"chunk": final_answer}
                ) + "\n\n"

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
                        req_dict = req.model_dump()

                        from src.agents.planning import planner
                        async for chunk in planner.stream_plan(req_dict):
                            if chunk["type"] == "plan":
                                req_dict["plan"] = chunk["nodes"]
                                await heartbeat_queue.put({"type": "plan", "steps": chunk["nodes"]})

                        async for event in orchestration.run(
                            supervisor.execute_plan, req_dict, session_id
                        ):
                            await heartbeat_queue.put(event)
                    except Exception:
                        logger.exception("Error in drain_supervisor")
                        await heartbeat_queue.put({
                            "type": "error",
                            "code": "orchestration_failed",
                        })
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
                            public_steps = [
                                {
                                    "id": str(step.get("id", index + 1)),
                                    "index": index + 1,
                                    "status": "pending",
                                }
                                for index, step in enumerate(event.get("steps", []))
                            ]
                            yield f"event: plan\ndata: {json.dumps({'steps': public_steps})}\n\n"
                        elif event_type == "tool_result":
                            agentops.record_tool_call(
                                session_id,
                                event.get("agent", "unknown"),
                                duration_ms=0,
                                success=True,
                            )
                            agent_name = event.get('agent', 'unknown')
                            yield f"event: tool\ndata: {json.dumps({'agent': agent_name, 'status': 'completed'})}\n\n"
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

            if session_id and final_answer:
                await context.save_turn(session_id, "user", req.query)
                await context.save_turn(session_id, "assistant", final_answer)
                
                try:
                    from src.services.history import HistoryService
                    from src.memory.memo import memo_manager
                    
                    user_msg = {
                        "user_id": user_id,
                        "role": "user",
                        "content": req.query
                    }
                    if req.attachments:
                        user_msg["attachments"] = req.attachments

                    await HistoryService.add_message(session_id, user_msg)
                    await HistoryService.add_message(session_id, {
                        "user_id": user_id,
                        "role": "assistant",
                        "content": final_answer
                    })

                    mem_data = [
                        {"role": "user", "content": req.query},
                        {"role": "assistant", "content": final_answer}
                    ]
                    asyncio.create_task(memo_manager.add_memory(mem_data, user_id))

                except Exception:
                    logger.exception("Chat history persistence to database error")

            await _consume_upload_quota(req)
            agentops.record_session_end(session_id, "done")

        except Exception:
            logger.exception("Chat stream execution unexpected error")
            agentops.record_session_end(session_id, "failed")
            yield f"event: error\ndata: {json.dumps({'code': 'chat_stream_failed'})}\n\n"

        yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(response_generator(), media_type="text/event-stream")


@router.get("/tuy-chon-ca-nhan")
async def get_user_instructions(
    current_user: CurrentUser = Depends(get_current_user),
):
    user_id = str(current_user.id)
    db = database.mongodb[settings.AGENTIC_AI_DB_NAME]
    doc = await db.user_instructions.find_one({"_id": user_id})
    instructions = doc.get("instructions", "") if doc else ""
    return {"status": "success", "data": {"instructions": instructions}}


@router.post("/tuy-chon-ca-nhan")
async def save_user_instructions(
    req: dict,
    current_user: CurrentUser = Depends(get_current_user),
):
    user_id = str(current_user.id)
    instructions = req.get("instructions", "").strip()
    db = database.mongodb[settings.AGENTIC_AI_DB_NAME]
    await db.user_instructions.update_one(
        {"_id": user_id},
        {
            "$set": {
                "instructions": instructions,
                "updated_at": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )
    return {
        "status": "success",
        "message_code": "user_instructions_updated",
        "data": {"instructions": instructions},
    }


@router.delete("/tuy-chon-ca-nhan")
async def clear_user_instructions(
    current_user: CurrentUser = Depends(get_current_user),
):
    user_id = str(current_user.id)
    db = database.mongodb[settings.AGENTIC_AI_DB_NAME]
    await db.user_instructions.delete_one({"_id": user_id})
    return {
        "status": "success",
        "message_code": "user_instructions_cleared",
    }
