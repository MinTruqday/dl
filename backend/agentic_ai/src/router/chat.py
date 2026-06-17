import asyncio
import json
from core.config import settings
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from loguru import logger
from src.agents.semantic_router import semantic_router
from src.core.llm_factory import llm_factory
from src.core.prompts import PromptType, prompt_registry
from src.harness.agentops_harness import agentops_harness
from src.harness.context_harness import context_harness
from src.harness.orchestration_harness import orchestration_harness
from src.harness.security_harness import security_harness
from src.schemas.requests import ChatRequest
from src.tools.tools import _make_api_request
from src.workflow.supervisor import supervisor

router = APIRouter(prefix='/tro-chuyen')

_USER_FACING_BLOCKED = 'Yêu cầu của bạn chứa nội dung không được phép, hệ thống không thể xử lý'
_USER_FACING_DOC_FORBIDDEN = 'Tài liệu yêu cầu không tồn tại hoặc bạn chưa có quyền truy cập'
_USER_FACING_GENERAL_ERROR = 'Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau'


@router.post('/tro-chuyen')
async def chat_endpoint(req: ChatRequest, request: Request):
    token = request.headers.get('Authorization')
    if token:
        req.token = token.replace('Bearer ', '')

    scan = security_harness.scan_input(req.query, user_id=req.user_id or '')
    if not scan.passed:
        return {'answer': _USER_FACING_BLOCKED, 'route': 'blocked'}

    req.query = scan.sanitized_text

    try:
        if req.document_ids:
            for doc_id in req.document_ids:
                try:
                    doc_res = await _make_api_request('GET', f'{settings.CONTENT_URL}/tai-lieu/{doc_id}', headers={'Authorization': f'Bearer {req.token}'}, timeout=settings.DEFAULT_HTTP_TIMEOUT)
                    if doc_res.status_code not in [200, 201]:
                        return {'answer': _USER_FACING_DOC_FORBIDDEN, 'route': 'error'}
                except Exception:
                    logger.exception('chat_endpoint_document_access_failed')
                    return {'answer': _USER_FACING_DOC_FORBIDDEN, 'route': 'error'}

        route_data = await semantic_router.execute(req.query)
        route = route_data['route']
        final_answer = ''

        if route == 'chat':
            final_answer = route_data.get('answer', '')
            if not final_answer:
                chat_llm = llm_factory.get_llm(req.ai_tier, req.role)
                text_prompt = prompt_registry.get(PromptType.CHAT_ASSISTANT).format(query=req.query)
                content = [{'type': 'text', 'text': text_prompt}, {'type': 'image_url', 'image_url': {'url': req.image_data}}] if req.image_data else text_prompt
                res = await chat_llm.ainvoke([HumanMessage(content=content)])
                final_answer = res.content
        else:
            async for event in supervisor.execute_plan(req):
                if event['type'] == 'message':
                    final_answer += event.get('chunk', '')

        final_answer = security_harness.scan_output(final_answer)
        return {'answer': final_answer or _USER_FACING_GENERAL_ERROR, 'route': 'agentic_ai'}
    except Exception:
        logger.exception('chat_endpoint_unexpected_failure')
        return {'answer': _USER_FACING_GENERAL_ERROR, 'route': 'error'}


@router.post('/truc-tiep')
async def stream_endpoint(req: ChatRequest, request: Request):
    token = request.headers.get('Authorization')
    bearer_token = token.replace('Bearer ', '') if token else None

    async def response_generator():
        if bearer_token:
            req.token = bearer_token

        session_id = req.session_id or ''
        user_id = req.user_id or ''

        scan = security_harness.scan_input(req.query, session_id=session_id, user_id=user_id)
        if not scan.passed:
            agentops_harness.record_security_event(session_id, 'prompt_injection_blocked', scan.risk_score, scan.violations)
            yield f"event: message\ndata: {json.dumps({'chunk': _USER_FACING_BLOCKED})}\n\n"
            yield 'event: done\ndata: [DONE]\n\n'
            return

        if scan.violations:
            agentops_harness.record_security_event(session_id, 'pii_redacted', scan.risk_score, scan.violations)

        req.query = scan.sanitized_text
        agentops_harness.record_session_start(session_id, user_id, req.query)

        hb_task = None
        exec_task = None
        final_answer = ''

        try:
            if req.document_ids:
                for doc_id in req.document_ids:
                    try:
                        doc_res = await _make_api_request('GET', f'{settings.CONTENT_URL}/tai-lieu/{doc_id}', headers={'Authorization': f'Bearer {req.token}'}, timeout=settings.DEFAULT_HTTP_TIMEOUT)
                        if doc_res.status_code not in [200, 201]:
                            yield f"event: message\ndata: {json.dumps({'chunk': _USER_FACING_DOC_FORBIDDEN})}\n\n"
                            agentops_harness.record_session_end(session_id, 'failed')
                            return
                    except Exception:
                        logger.exception('stream_endpoint_document_access_failed')
                        yield f"event: message\ndata: {json.dumps({'chunk': _USER_FACING_DOC_FORBIDDEN})}\n\n"
                        agentops_harness.record_session_end(session_id, 'failed')
                        return

            ctx = await context_harness.build_context(session_id=session_id, user_id=user_id, query=req.query, document_ids=req.document_ids)
            req.conversation_history = ctx.chat_history

            route_data = await semantic_router.execute(req.query)
            route = route_data['route']

            if route == 'chat':
                yield f"event: status\ndata: {json.dumps({'node': 'Hệ thống đang phản hồi trực tiếp yêu cầu của bạn'})}\n\n"
                fast_answer = route_data.get('answer', '')
                if fast_answer:
                    yield f"event: message\ndata: {json.dumps({'chunk': fast_answer})}\n\n"
                    final_answer = fast_answer
                else:
                    chat_llm = llm_factory.get_llm(req.ai_tier, req.role)
                    text_prompt = prompt_registry.get(PromptType.CHAT_ASSISTANT).format(query=req.query)
                    content = [{'type': 'text', 'text': text_prompt}, {'type': 'image_url', 'image_url': {'url': req.image_data}}] if req.image_data else text_prompt
                    async for chunk in chat_llm.astream([HumanMessage(content=content)]):
                        if chunk.content:
                            final_answer += chunk.content
                            yield f"event: message\ndata: {json.dumps({'chunk': chunk.content})}\n\n"
            else:
                heartbeat_queue: asyncio.Queue = asyncio.Queue()

                async def heartbeat_sender():
                    try:
                        while True:
                            await asyncio.sleep(10)
                            await heartbeat_queue.put({'type': 'heartbeat'})
                    except asyncio.CancelledError:
                        return

                async def drain_supervisor():
                    try:
                        async for event in orchestration_harness.run(supervisor.execute_plan, req, session_id):
                            await heartbeat_queue.put(event)
                    finally:
                        await heartbeat_queue.put({'type': '__done__'})

                hb_task = asyncio.create_task(heartbeat_sender())
                exec_task = asyncio.create_task(drain_supervisor())

                try:
                    while True:
                        event = await heartbeat_queue.get()
                        event_type = event['type']

                        if event_type == '__done__':
                            break
                        elif event_type == 'heartbeat':
                            yield 'event: heartbeat\ndata: {}\n\n'
                        elif event_type == 'status':
                            yield f"event: status\ndata: {json.dumps({'node': event['node']})}\n\n"
                        elif event_type == 'plan':
                            yield f"event: plan\ndata: {json.dumps({'steps': event['steps']})}\n\n"
                        elif event_type == 'tool_result':
                            agentops_harness.record_tool_call(session_id, event.get('agent', 'unknown'), duration_ms=0, success=True)
                            yield f"event: tool\ndata: {json.dumps({'agent': event['agent'], 'result': event.get('content', '')})}\n\n"
                        elif event_type == 'message':
                            final_answer += event['chunk']
                            yield f"event: message\ndata: {json.dumps({'chunk': event['chunk']})}\n\n"
                        elif event_type == 'error':
                            yield f"event: message\ndata: {json.dumps({'chunk': event['message']})}\n\n"
                finally:
                    for task in (hb_task, exec_task):
                        if task and not task.done():
                            task.cancel()
                    await asyncio.gather(*(t for t in (hb_task, exec_task) if t is not None), return_exceptions=True)

            if final_answer:
                final_answer = security_harness.scan_output(final_answer, session_id=session_id)

            if session_id and final_answer:
                await context_harness.save_turn(session_id, 'user', req.query)
                await context_harness.save_turn(session_id, 'assistant', final_answer)

            agentops_harness.record_session_end(session_id, 'done')

        except Exception:
            logger.exception('stream_endpoint_unexpected_failure')
            agentops_harness.record_session_end(session_id, 'failed')
            yield f"event: message\ndata: {json.dumps({'chunk': _USER_FACING_GENERAL_ERROR})}\n\n"

        yield 'event: done\ndata: [DONE]\n\n'

    return StreamingResponse(response_generator(), media_type='text/event-stream')