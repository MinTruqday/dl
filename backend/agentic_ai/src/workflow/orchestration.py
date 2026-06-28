import time
from typing import Any, Dict, List, Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from loguru import logger
from pydantic import BaseModel, Field
from src.agents.sandbox import actor
from src.agents.interpreter import interpreter
from src.agents.plan import planner
from src.agents.reasoning import reasoner
from src.agents.analysis import researcher
from src.agents.generation import response_generator
from src.agents.engine import search_engine
from src.workflow.state import ActingState
from uuid6 import uuid7

from src.schemas.model import TaskEvaluation

async def supervisor_node(state: ActingState):
    start_time = state.get("start_time")
    if not start_time:
        start_time = time.time()

    if time.time() - start_time > 45:
        logger.exception("Quá thời gian thực thi tác vụ AI")
        return {
            "next_node": "trimmer",
            "error": "Yêu cầu quá phức tạp, vượt giới hạn thời gian xử lý",
        }

    steps = state.get("steps", [])
    idx = state.get("current_step_index", 0)
    replan_count = state.get("replan_count", 0)

    if replan_count > 6:
        return {
            "steps": steps,
            "current_step_index": len(steps),
            "next_node": "trimmer",
            "error": "Trí tuệ nhân tạo vượt quá số bước thực thi",
        }

    if not steps:
        steps = await planner.create_plan(state["req_data"])
        idx = 0

    if state.get("error"):
        logger.warning("Bỏ qua các bước tiếp theo do lỗi trước đó")
        return {
            "steps": steps,
            "current_step_index": len(steps),
            "next_node": "trimmer",
            "start_time": start_time,
        }

    if idx >= len(steps):
        return {"steps": steps, "current_step_index": idx, "next_node": "trimmer"}

    current_step = steps[idx]
    agent_name = current_step.get("agent", "Action")

    route_map = {
        "InterpreterAgent": "interpreter",
        "EngineAgent": "search_engine",
        "Action": "action",
        "Knowledge": "knowledge",
        "Reasoning": "reasoning",
    }

    next_node = route_map.get(agent_name, "action")
    return {"steps": steps, "current_step_index": idx, "next_node": next_node}

async def execute_tool_node(state: ActingState, tool_callable, agent_name: str):
    idx = state.get("current_step_index", 0)
    steps = state.get("steps", [])

    if idx >= len(steps):
        return {"current_step_index": idx + 1}

    step = steps[idx]
    current_task = step.get("task", "")
    req_data = state.get("req_data", {})

    try:
        from src.workflow.graph import llm

        evaluator_llm = llm.with_structured_output(TaskEvaluation)

        replan_count = 0
        final_res = ""

        while replan_count < 3:
            if agent_name == "Action":
                token = req_data.get("token")
                user_id = req_data.get("user_id")
                res = await tool_callable.execute(current_task, {}, user_id, token)
            elif agent_name == "Knowledge":
                res = await tool_callable.execute(req_data)
            else:
                res = await tool_callable.execute(current_task)

            from src.core.registry import PromptType, registry

            prompt_template = registry.get(PromptType.SELF_REFLECTION)
            prompt = prompt_template.format(res=res)

            try:
                eval_res = await evaluator_llm.ainvoke(prompt)

                if eval_res.status == "FAIL":
                    replan_count += 1
                    logger.warning("Tự đánh giá thất bại, đang tạo lại kế hoạch")
                    current_task = eval_res.revised_task or current_task
                    final_res = res
                else:
                    final_res = res
                    break
            except Exception as e:
                logger.debug(f"Lỗi phân tích kết quả đánh giá: {e}")
                final_res = res
                break

        if replan_count >= 3:
            final_res = "The agent was unable to complete the task"

        return {
            "current_step_index": idx + 1,
            "consolidated_results": [f"[{agent_name} - Step {idx+1}]:\n{final_res}"],
            "last_agent_result": final_res,
        }
    except Exception as e:
        logger.exception(f"Lỗi máy chủ thực thi: {e}")
        return {
            "consolidated_results": ["The execution step failed"],
            "error": "Internal processing error",
        }

async def code_interpreter_node(state: ActingState):
    return await execute_tool_node(state, interpreter, "InterpreterAgent")

async def search_engine_node(state: ActingState):
    return await execute_tool_node(state, search_engine, "EngineAgent")

async def actor_agent_node(state: ActingState):
    return await execute_tool_node(state, actor, "Action")

async def researcher_agent_node(state: ActingState):
    return await execute_tool_node(state, researcher, "Knowledge")

async def reasoner_agent_node(state: ActingState):
    return await execute_tool_node(state, reasoning, "Reasoning")

async def trimmer_node(state: ActingState):
    results = state.get("consolidated_results", [])
    if not results:
        return {"next_node": "trimmer"}

    total_length = sum(len(str(r)) for r in results)
    if total_length > 12000:
        logger.info("Đang tổng hợp kết quả")
        try:
            from src.workflow.graph import llm

            combined = "\n\n".join(str(r) for r in results)
            summary_prompt = (
                f"Summarize concisely preserving facts IDs data:\n\n{combined[:20000]}"
            )
            summary_res = await llm.ainvoke(summary_prompt)
            trimmed = summary_res.content.strip()
        except Exception as e:
            logger.exception(f"Lỗi rút gọn tóm tắt: {e}")
            trimmed = "\n\n".join(str(r) for r in results)[:12000]
        return {"consolidated_results": [trimmed], "next_node": "trimmer"}

    return {"next_node": "trimmer"}

def trimmer_router(state: ActingState):
    return state.get("next_node", "aggregator")

async def sanitizer_node(state: ActingState):
    return {"next_node": "trimmer"}

async def aggregator_node(state: ActingState):
    return {"final_answer": ""}

def router(state: ActingState):
    return state.get("next_node", "aggregator")

workflow = StateGraph(ActingState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("interpreter", code_interpreter_node)
workflow.add_node("search_engine", search_engine_node)
workflow.add_node("action", actor_agent_node)
workflow.add_node("knowledge", researcher_agent_node)
workflow.add_node("reasoning", reasoner_agent_node)
workflow.add_node("trimmer", trimmer_node)
workflow.add_node("sanitizer", sanitizer_node)
workflow.add_node("aggregator", aggregator_node)

workflow.set_entry_point("supervisor")

workflow.add_conditional_edges(
    "supervisor",
    router,
    {
        "interpreter": "interpreter",
        "search_engine": "search_engine",
        "action": "action",
        "knowledge": "knowledge",
        "reasoning": "reasoning",
        "aggregator": "aggregator",
        "trimmer": "trimmer",
    },
)

for node in ["interpreter", "search_engine", "action", "knowledge", "reasoning"]:
    workflow.add_edge(node, "supervisor")

workflow.add_conditional_edges("trimmer", trimmer_router, {"aggregator": "sanitizer"})
workflow.add_edge("sanitizer", "aggregator")
workflow.add_edge("aggregator", END)

memory = MemorySaver()
supervisor_app = workflow.compile(checkpointer=memory, interrupt_before=["action"])

class OrchestrationWorkflow:
    def __init__(self):
        self.app = supervisor_app

    async def execute_plan(self, req_data):
        logger.info("Khởi tạo luồng thực thi")
        yield {"type": "status", "node": "The system is analyzing your request"}

        initial_state = {
            "req_data": req_data,
            "steps": [],
            "current_step_index": 0,
            "consolidated_results": [],
            "final_answer": "",
            "next_node": "",
            "error": "",
            "replan_count": 0,
        }

        final_results = []
        session_id = req_data.get("session_id", str(uuid7()))
        config = {
            "configurable": {"thread_id": session_id},
            "recursion_limit": 25,
        }

        async for output in self.app.astream(initial_state, config=config):
            for node_name, state_update in output.items():
                if "consolidated_results" in state_update:
                    final_results = state_update["consolidated_results"]

                if node_name == "supervisor":
                    steps = state_update.get("steps")
                    if steps and state_update.get("current_step_index") == 0:
                        yield {"type": "plan", "steps": steps}
                elif node_name in [
                    "interpreter",
                    "search_engine",
                    "action",
                    "knowledge",
                    "reasoning",
                ]:
                    if state_update.get("error"):
                        yield {"type": "error", "message": "Đã xảy ra một lỗi bất thường trong quá trình xử lý luồng dữ liệu"}
                    else:
                        yield {
                            "type": "tool_result",
                            "agent": node_name,
                            "content": state_update.get(
                                "last_agent_result", "Completed"
                            ),
                        }

                elif node_name == "aggregator":
                    yield {"type": "status", "node": "Synthesizing information"}

        if not final_results:
            final_results = ["Unable to locate data"]

        query = req_data.get("query", "")
        async for chunk in response_generator.aggregate_stream(query, final_results):
            yield {"type": "message", "chunk": chunk}

supervisor = OrchestrationWorkflow()
