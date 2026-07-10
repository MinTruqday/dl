import json

import httpx
from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from loguru import logger
from src.agents.route import semantic_router
from src.core.infrastructure.configuration import settings
from src.core.registry import PromptType, registry
from src.harness.agentops import agentops
from src.harness.context import context
from src.harness.orchestration import orchestration
from src.harness.security import security
from src.schemas.interaction import ChatRequest
from src.workflow.orchestration import supervisor

router = APIRouter(route_class=LoggingRoute, prefix="/tro-chuyen")

@router.post("")
async def chat_endpoint(req: ChatRequest, request: Request):
    logger.info(f"Started Chat streaming process. Input data {req.model_dump(exclude={'token', 'user_id'})}")
    token = request.headers.get("Authorization")
    if token:
        req.token = token.replace("Bearer ", "")

    scan = await security.ascan_input(req.query, user_id=req.user_id or "")
    if not scan.passed:
        logger.warning("Query execution blocked due to security policy violation")
        return {
            "answer": "Nội dung yêu cầu vi phạm chính sách bảo mật và không thể xử lý",
            "route": "blocked",
        }

    req.query = scan.sanitized_text

    try:
        if req.document_ids:
            from src.tools.interface import INTERNAL_API_URL, _make_api_request

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
                            "answer": "Tài liệu không tồn tại hoặc bạn không có quyền truy cập",
                            "route": "error",
                        }
                except Exception as e:
                    logger.exception(f"Document {doc_id} access verification error")
                    return {
                        "answer": "Hệ thống tạm thời không thể xác minh quyền truy cập tài liệu",
                        "route": "error",
                    }

        route_data = await semantic_router.execute(req.query)
        if req.useSmart:
            route = "supervisor"
        else:
            route = "chat"
            
        final_answer = ""

        if route == "chat":
            final_answer = route_data.get("answer", "")
            if not final_answer:
                from huggingface_hub import AsyncInferenceClient
                from langchain_core.messages import HumanMessage
                from src.utils.huggingface import HFInferenceChat

                from src.core.infrastructure.configuration import settings

                llama_client = AsyncInferenceClient(
                    model=settings.LLAMA_MODEL, token=settings.HF_TOKEN
                )
                chat_llm = HFInferenceChat(
                    client=llama_client, model=settings.LLAMA_MODEL
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

                res = await chat_llm.ainvoke([HumanMessage(content=content)])
                final_answer = res.content
        else:
            async for event in supervisor.execute_plan(req.model_dump()):
                if event["type"] == "message":
                    final_answer += event.get("chunk", "")

        final_answer = await security.ascan_output(final_answer)
        return {
            "answer": final_answer or "Hệ thống tạm thời không thể phản hồi, vui lòng thử lại sau",
            "route": "agentic_ai",
        }
    except Exception as e:
        logger.exception("AI agent workflow execution error")
        return {
            "answer": "Hệ thống gặp sự cố bất ngờ trong quá trình tổng hợp dữ liệu, vui lòng thử lại sau",
            "route": "error",
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
        return True, ""
        
    try:
        from src.core.infrastructure.database import database
        user = await database.mongodb[settings.SERVICE_DB_NAME].users.find_one({"_id": req.user_id})
        ai_tier = user.get("ai_tier", "BASIC") if user else "BASIC"
        is_admin = user.get("role") == "admin" if user else False
        
        if is_admin or ai_tier != "BASIC":
            return True, ""

        async with httpx.AsyncClient(timeout=10.0) as c:
            resp = await c.get(
                f"{settings.USAGE_URL}/han-muc/tai-len/xac-minh",
                params={"item_type": item_type},
                headers={"Authorization": f"Bearer {req.token}"} if req.token else {}
            )
            if resp.status_code != 200:
                detail = resp.json().get("detail") or "Tài khoản của bạn đã vượt mức giới hạn dung lượng tải lên"
                return False, detail
            return True, ""
    except Exception as e:
        logger.exception("Upload quota verification error")
        return False, "Hệ thống tạm thời không thể xác minh dung lượng lưu trữ"

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
        user = await database.mongodb[settings.SERVICE_DB_NAME].users.find_one({"_id": req.user_id})
        ai_tier = user.get("ai_tier", "BASIC") if user else "BASIC"
        is_admin = user.get("role") == "admin" if user else False
        
        if is_admin or ai_tier != "BASIC":
            return

        async with httpx.AsyncClient(timeout=10.0) as c:
            await c.post(
                f"{settings.USAGE_URL}/han-muc/tai-len/tieu-thu",
                json={"user_id": req.user_id, "item_type": item_type, "req_reset_hours": 24},
                headers={"Authorization": f"Bearer {req.token}"} if req.token else {}
            )
    except Exception as e:
        logger.exception("Upload quota consumption error")

@router.post("/phat-truc-tiep")
async def stream_endpoint(req: ChatRequest, request: Request):
    logger.info(f"Started Server-Sent Events stream. Input data {req.model_dump(exclude={'token', 'user_id'})}")
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
            yield f"event: message\ndata: {json.dumps({'chunk': 'Nội dung yêu cầu chứa dữ liệu vi phạm chính sách bảo mật và không thể xử lý'})}\n\n"
            yield "event: done\ndata: [DONE]\n\n"
            return

        if scan.violations:
            agentops.record_security_event(
                session_id, "pii_redacted", scan.risk_score, scan.violations
            )

        req.query = scan.sanitized_text

        agentops.record_session_start(session_id, user_id, req.query)

        try:
            is_quota_ok, quota_msg = await _check_upload_quota(req)
            if not is_quota_ok:
                yield f"event: message\ndata: {json.dumps({'chunk': quota_msg})}\n\n"
                yield "event: done\ndata: [DONE]\n\n"
                agentops.record_session_end(session_id, "failed")
                return

            if req.document_ids:
                from src.tools.interface import INTERNAL_API_URL, _make_api_request

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
                            yield f"event: message\ndata: {json.dumps({'chunk': 'Tài liệu không tồn tại hoặc bạn không có quyền truy cập'})}\n\n"
                            agentops.record_session_end(session_id, "failed")
                            return
                    except Exception as e:
                        logger.exception(f"Document {doc_id} access verification error")
                        yield f"event: message\ndata: {json.dumps({'chunk': 'Hệ thống tạm thời không thể xác minh quyền truy cập tài liệu'})}\n\n"
                        agentops.record_session_end(session_id, "failed")
                        return

            ctx = await context.build_context(
                session_id=session_id,
                user_id=user_id,
                query=req.query,
                document_ids=req.document_ids,
            )
            req.conversation_history = ctx.chat_history

            route_data = await semantic_router.execute(req.query)
            if req.useSmart:
                route = "supervisor"
            else:
                route = "chat"
                
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
                        model=settings.LLAMA_MODEL, token=settings.HF_TOKEN
                    )
                    chat_llm = HFInferenceChat(
                        client=llama_client, model=settings.LLAMA_MODEL
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

                    async for chunk in chat_llm.astream(
                        [HumanMessage(content=content)]
                    ):
                        if chunk.content:
                            final_answer += chunk.content
                            yield f"event: message\ndata: {json.dumps({'chunk': chunk.content})}\n\n"

            else:
                import asyncio

                heartbeat_queue: asyncio.Queue = asyncio.Queue()

                async def heartbeat_sender():
                    while True:
                        await asyncio.sleep(10)
                        await heartbeat_queue.put({"type": "heartbeat"})

                hb_task = asyncio.create_task(heartbeat_sender())

                async def drain_supervisor():
                    async for event in orchestration.run(
                        supervisor.execute_plan, req.model_dump(), session_id
                    ):
                        await heartbeat_queue.put(event)
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
                            yield f"event: status\ndata: {json.dumps({'node': event['node']})}\n\n"
                        elif event_type == "plan":
                            yield f"event: plan\ndata: {json.dumps({'steps': event['steps']})}\n\n"
                        elif event_type == "tool_result":
                            agentops.record_tool_call(
                                session_id,
                                event.get("agent", "unknown"),
                                duration_ms=0,
                                success=True,
                            )
                            yield f"event: tool\ndata: {json.dumps({'agent': event['agent'], 'result': event.get('content', 'Completed')})}\n\n"
                        elif event_type == "message":
                            final_answer += event["chunk"]
                            yield f"event: message\ndata: {json.dumps({'chunk': event['chunk']})}\n\n"
                        elif event_type == "error":
                            yield f"event: message\ndata: {json.dumps({'chunk': event['message']})}\n\n"
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
                except Exception as e:
                    logger.exception("Chat history persistence to database error")

            await _consume_upload_quota(req)
            agentops.record_session_end(session_id, "done")

        except Exception as e:
            logger.exception("Chat stream execution unexpected error")
            agentops.record_session_end(session_id, "failed")
            yield f"event: message\ndata: {json.dumps({'chunk': 'Hệ thống gặp sự cố bất ngờ trong quá trình thực thi, vui lòng thử lại sau'})}\n\n"

        yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(response_generator(), media_type="text/event-stream")
