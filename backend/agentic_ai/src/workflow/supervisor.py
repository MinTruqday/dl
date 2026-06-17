import time
from typing import Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from loguru import logger
from pydantic import BaseModel, Field
from src.agents.action import action
from src.agents.code_interpreter import code_interpreter
from src.agents.knowledge import knowledge
from src.agents.planning import planning
from src.agents.reasoning import reasoning
from src.agents.response_generator import response_generator
from src.agents.search_engine import search_engine
from src.core.exceptions import AgenticError
from src.core.prompts import PromptType, prompt_registry
from src.workflow.graph import llm
from src.workflow.state import ActingState
from uuid6 import uuid7

_SESSION_TIMEOUT_SECONDS = 45
_MAX_REPLAN = 6
_MAX_RETRY_PER_STEP = 3
_TRIM_THRESHOLD = 12000
_TRIM_SUMMARY_CAP = 20000
_ROUTE_MAP = {
    'CodeInterpreter': 'code_interpreter',
    'SearchEngine': 'search_engine',
    'Action': 'action',
    'Knowledge': 'knowledge',
    'Reasoning': 'reasoning',
}


class TaskEvaluation(BaseModel):
    status: Literal['PASS', 'FAIL'] = Field(description='Operational status determining outcome success or failure')
    feedback: str = Field(description='Detailed structural feedback explaining functional operational outcome')
    revised_task: str = Field(default='', description='Revised executable task parameters provided upon validation failure')


async def supervisor_node(state: ActingState):
    start_time = state.get('start_time') or time.time()

    if time.time() - start_time > _SESSION_TIMEOUT_SECONDS:
        logger.warning('supervisor_timeout_exceeded')
        return {'next_node': 'aggregator', 'error': 'session_timeout', 'start_time': start_time}

    steps = state.get('steps', [])
    idx = state.get('current_step_index', 0)
    replan_count = state.get('replan_count', 0)

    if replan_count > _MAX_REPLAN:
        logger.warning('supervisor_replan_threshold_exceeded')
        return {'steps': steps, 'current_step_index': len(steps), 'next_node': 'aggregator', 'error': 'replan_exhausted', 'start_time': start_time}

    if not steps:
        steps = await planning.create_plan(state['req_data'])
        idx = 0

    if state.get('error'):
        return {'steps': steps, 'current_step_index': len(steps), 'next_node': 'aggregator', 'start_time': start_time}

    if idx >= len(steps):
        return {'steps': steps, 'current_step_index': idx, 'next_node': 'aggregator', 'start_time': start_time}

    current_step = steps[idx]
    agent_name = current_step.get('agent', 'Action')
    next_node = _ROUTE_MAP.get(agent_name, 'action')
    return {'steps': steps, 'current_step_index': idx, 'next_node': next_node, 'start_time': start_time}


async def execute_tool_node(state: ActingState, tool_callable, agent_name: str):
    idx = state.get('current_step_index', 0)
    steps = state.get('steps', [])

    if idx >= len(steps):
        return {'current_step_index': idx + 1}

    step = steps[idx]
    current_task = step.get('task', '')
    req_data = state.get('req_data', {})

    try:
        evaluator_llm = llm.with_structured_output(TaskEvaluation)
        retry_count = 0
        final_res = ''

        while retry_count < _MAX_RETRY_PER_STEP:
            try:
                if agent_name == 'Action':
                    token = req_data.get('token')
                    user_id = req_data.get('user_id')
                    res = await tool_callable.execute(current_task, {}, user_id, token)
                elif agent_name == 'Knowledge':
                    res = await tool_callable.execute(req_data)
                else:
                    res = await tool_callable.execute(current_task)
            except AgenticError as ae:
                logger.warning(f'execute_tool_node_agent_error agent={agent_name} error={ae}')
                final_res = ae.user_message
                break

            try:
                prompt = prompt_registry.get(PromptType.SELF_REFLECTION).format(res=res)
                eval_res = await evaluator_llm.ainvoke(prompt)
                if eval_res.status == 'FAIL':
                    retry_count += 1
                    logger.warning(f'execute_tool_node_self_reflection_fail agent={agent_name} attempt={retry_count}')
                    current_task = eval_res.revised_task or current_task
                    final_res = res
                else:
                    final_res = res
                    break
            except Exception:
                logger.exception('execute_tool_node_self_reflection_failed')
                final_res = res
                break

        if retry_count >= _MAX_RETRY_PER_STEP:
            final_res = final_res or 'Hệ thống không thể hoàn tất bước xử lý này, vui lòng thử lại sau'

        return {
            'current_step_index': idx + 1,
            'consolidated_results': [f'[{agent_name} - Step {idx+1}]:\n{final_res}'],
            'last_agent_result': final_res,
        }
    except Exception:
        logger.exception('execute_tool_node_unexpected_failure')
        return {
            'consolidated_results': [f'[{agent_name} - Step {idx+1}]: Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau'],
            'error': 'tool_execution_error',
        }


async def code_interpreter_node(state: ActingState):
    return await execute_tool_node(state, code_interpreter, 'CodeInterpreter')


async def search_engine_node(state: ActingState):
    return await execute_tool_node(state, search_engine, 'SearchEngine')


async def action_agent_node(state: ActingState):
    return await execute_tool_node(state, action, 'Action')


async def knowledge_agent_node(state: ActingState):
    return await execute_tool_node(state, knowledge, 'Knowledge')


async def reasoning_agent_node(state: ActingState):
    return await execute_tool_node(state, reasoning, 'Reasoning')


async def trimmer_node(state: ActingState):
    results = state.get('consolidated_results', [])
    if not results:
        return {'next_node': 'sanitizer'}
    total_length = sum(len(str(r)) for r in results)
    if total_length > _TRIM_THRESHOLD:
        try:
            combined = '\n\n'.join(str(r) for r in results)
            summary_prompt = f'Summarize concisely preserving facts IDs data:\n\n{combined[:_TRIM_SUMMARY_CAP]}'
            summary_res = await llm.ainvoke(summary_prompt)
            trimmed = (summary_res.content or '').strip()
        except Exception:
            logger.exception('trimmer_node_summary_failed')
            trimmed = '\n\n'.join(str(r) for r in results)[:_TRIM_THRESHOLD]
        return {'consolidated_results': [trimmed], 'next_node': 'sanitizer'}
    return {'next_node': 'sanitizer'}


async def sanitizer_node(state: ActingState):
    return {'next_node': 'aggregator'}


async def aggregator_node(state: ActingState):
    return {'final_answer': ''}


def router(state: ActingState):
    return state.get('next_node', 'aggregator')


def trimmer_router(state: ActingState):
    return state.get('next_node', 'sanitizer')


workflow = StateGraph(ActingState)
workflow.add_node('supervisor', supervisor_node)
workflow.add_node('code_interpreter', code_interpreter_node)
workflow.add_node('search_engine', search_engine_node)
workflow.add_node('action', action_agent_node)
workflow.add_node('knowledge', knowledge_agent_node)
workflow.add_node('reasoning', reasoning_agent_node)
workflow.add_node('trimmer', trimmer_node)
workflow.add_node('sanitizer', sanitizer_node)
workflow.add_node('aggregator', aggregator_node)

workflow.set_entry_point('supervisor')

workflow.add_conditional_edges(
    'supervisor',
    router,
    {
        'code_interpreter': 'code_interpreter',
        'search_engine': 'search_engine',
        'action': 'action',
        'knowledge': 'knowledge',
        'reasoning': 'reasoning',
        'aggregator': 'trimmer',
        'trimmer': 'trimmer',
    },
)

for node in ['code_interpreter', 'search_engine', 'action', 'knowledge', 'reasoning']:
    workflow.add_edge(node, 'supervisor')

workflow.add_conditional_edges('trimmer', trimmer_router, {'sanitizer': 'sanitizer'})
workflow.add_edge('sanitizer', 'aggregator')
workflow.add_edge('aggregator', END)

memory = MemorySaver()
supervisor_app = workflow.compile(checkpointer=memory, interrupt_before=['action'])


class Supervisor:
    def __init__(self):
        self.app = supervisor_app

    async def execute_plan(self, req_data):
        if hasattr(req_data, 'model_dump'):
            payload = req_data.model_dump()
        elif isinstance(req_data, dict):
            payload = req_data
        else:
            payload = dict(req_data)

        logger.info(f"supervisor_execute_plan_started session={payload.get('session_id', '')}")
        yield {'type': 'status', 'node': 'Hệ thống đang phân tích yêu cầu của bạn'}

        initial_state = {
            'req_data': payload,
            'steps': [],
            'current_step_index': 0,
            'consolidated_results': [],
            'final_answer': '',
            'next_node': '',
            'error': '',
            'replan_count': 0,
            'start_time': time.time(),
        }

        final_results = []
        session_id = payload.get('session_id') or str(uuid7())
        config = {'configurable': {'thread_id': session_id}, 'recursion_limit': 25}

        try:
            async for output in self.app.astream(initial_state, config=config):
                for node_name, state_update in output.items():
                    if 'consolidated_results' in state_update and state_update['consolidated_results']:
                        final_results = state_update['consolidated_results']

                    if node_name == 'supervisor':
                        steps = state_update.get('steps')
                        if steps and state_update.get('current_step_index') == 0:
                            yield {'type': 'plan', 'steps': steps}
                    elif node_name in ['code_interpreter', 'search_engine', 'action', 'knowledge', 'reasoning']:
                        if state_update.get('error'):
                            yield {'type': 'error', 'message': 'Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau'}
                        else:
                            yield {'type': 'tool_result', 'agent': node_name, 'content': state_update.get('last_agent_result', '')}
                    elif node_name == 'aggregator':
                        yield {'type': 'status', 'node': 'Hệ thống đang tổng hợp kết quả'}
        except Exception:
            logger.exception('supervisor_execute_plan_failed')
            yield {'type': 'error', 'message': 'Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau'}

        if not final_results:
            final_results = ['Hệ thống chưa tìm thấy kết quả phù hợp với yêu cầu của bạn']

        query = payload.get('query', '')
        ai_tier = payload.get('ai_tier') or 'BASIC'
        role = payload.get('role') or 'reader'
        async for chunk in response_generator.aggregate_stream(query, final_results, ai_tier=ai_tier, role=role):
            yield {'type': 'message', 'chunk': chunk}


supervisor = Supervisor()