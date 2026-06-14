import time
from typing import Any, Dict, List, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import Send
from loguru import logger
from src.agents.action import action
from src.agents.code_interpreter import code_interpreter
from src.agents.knowledge import knowledge
from src.agents.planning import planning
from src.agents.reasoning import reasoning
from src.agents.response_generator import response_generator
from src.agents.search_engine import search_engine
from src.workflow.state import ActingState
from uuid6 import uuid7


async def supervisor_node(state: ActingState):
    start_time = state.get("start_time")
    if not start_time:
        start_time = time.time()

    if time.time() - start_time > 45:
        logger.error("Execution time exceeded the 45-second limit")
        return {
            "next_node": "trimmer",
            "error": "The request is too complex and has exceeded the processing time budget (45s)",
        }

    steps = state.get("steps", [])
    idx = state.get("current_step_index", 0)
    replan_count = state.get("replan_count", 0)

    if replan_count > 6:
        return {
            "steps": steps,
            "current_step_index": len(steps),
            "next_node": "trimmer",
            "error": "Tool budget exceeded",
        }

    if not steps:
        steps = await planning.create_plan(state["req"])
        idx = 0

    if state.get("error"):
        logger.warning("Skipping subsequent tools due to error")
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
        "CodeInterpreter": "code_interpreter",
        "SearchEngine": "search_engine",
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
    task_desc = step.get("task", "")
    req = state.get("req")

    try:
        from src.workflow.brain import llm

        replan_count = 0
        final_res = ""
        current_task = task_desc
        while replan_count < 3:
            if agent_name == "Action":
                token = getattr(req, "token", None)
                res = await tool_callable.execute(current_task, {}, req.user_id, token)
            elif agent_name == "Knowledge":
                res = await tool_callable.execute(req)
            else:
                res = await tool_callable.execute(current_task)

            from src.core.prompt_registry import PromptType, prompt_registry

            prompt_template = prompt_registry.get(PromptType.SELF_REFLECTION)
            prompt = prompt_template.format(res=res)
            eval_res = await llm.ainvoke(prompt)

            if "FAIL" in eval_res.content.upper():
                replan_count += 1
                logger.warning(
                    f"Self-evaluation failed for {agent_name}, replanning attempt {replan_count}/3"
                )
                replan_prompt = (
                    f"The following task failed:\n{current_task}\n\n"
                    f"Error result:\n{res}\n\n"
                    "Rewrite the task description to fix the issue. Output only the revised task"
                )
                replan_res = await llm.ainvoke(replan_prompt)
                current_task = replan_res.content.strip() or current_task
                final_res = res
            else:
                final_res = res
                break

        if replan_count >= 3:
            final_res = (
                f"Unable to execute this task after 3 attempts. Returned error:\n{final_res}"
            )

        return {
            "current_step_index": idx + 1,
            "consolidated_results": [
                f"Step {idx+1} result ({agent_name}):\n{final_res}"
            ],
            "last_agent_result": final_res,
        }
    except Exception as e:
        logger.error("Node execution failed")
        return {
            "consolidated_results": [f"Error at step {idx+1} ({agent_name}): {str(e)}"],
            "error": str(e),
        }


async def code_interpreter_node(state: ActingState):
    return await execute_tool_node(state, code_interpreter, "CodeInterpreter")


async def search_engine_node(state: ActingState):
    return await execute_tool_node(state, search_engine, "SearchEngine")


async def action_agent_node(state: ActingState):
    return await execute_tool_node(state, action, "Action")


async def knowledge_agent_node(state: ActingState):
    return await execute_tool_node(state, knowledge, "Knowledge")


async def reasoning_agent_node(state: ActingState):
    return await execute_tool_node(state, reasoning, "Reasoning")


async def trimmer_node(state: ActingState):
    results = state.get("consolidated_results", [])
    if not results:
        return {"next_node": "trimmer"}

    total_length = sum(len(str(r)) for r in results)
    if total_length > 12000:
        logger.info(
            f"Summarizing synthesized results (count: {total_length})"
        )
        try:
            from src.workflow.brain import llm

            combined = "\n\n".join(str(r) for r in results)
            summary_prompt = (
                "Summarize the following agent execution results concisely, "
                "preserving all key facts, numbers, IDs, and structured data. "
                "Output in the same language as the input.\n\n"
                f"{combined[:20000]}"
            )
            summary_res = await llm.ainvoke(summary_prompt)
            trimmed = summary_res.content.strip()
        except Exception as e:
            logger.warning(
                "Summarization failed, switching to truncation due to error"
            )
            trimmed = "\n\n".join(str(r) for r in results)[:12000]
        return {"consolidated_results": [trimmed], "next_node": "trimmer"}

    return {"next_node": "trimmer"}


def trimmer_router(state: ActingState):
    return state.get("next_node", "aggregator")


async def sanitizer_node(state: ActingState):
    req = state.get("req")
    if req:
        if hasattr(req, "token"):
            req.token = None
        if hasattr(req, "user_id"):
            req.user_id = None
        if hasattr(req, "session_id"):
            req.session_id = None
    return {"req": req, "next_node": "trimmer"}


async def aggregator_node(state: ActingState):
    return {"final_answer": ""}


def router(state: ActingState):
    return state.get("next_node", "aggregator")


workflow = StateGraph(ActingState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("code_interpreter", code_interpreter_node)
workflow.add_node("search_engine", search_engine_node)
workflow.add_node("action", action_agent_node)
workflow.add_node("knowledge", knowledge_agent_node)
workflow.add_node("reasoning", reasoning_agent_node)
workflow.add_node("trimmer", trimmer_node)
workflow.add_node("sanitizer", sanitizer_node)
workflow.add_node("aggregator", aggregator_node)

workflow.set_entry_point("supervisor")

workflow.add_conditional_edges(
    "supervisor",
    router,
    {
        "code_interpreter": "code_interpreter",
        "search_engine": "search_engine",
        "action": "action",
        "knowledge": "knowledge",
        "reasoning": "reasoning",
        "aggregator": "aggregator",
        "trimmer": "trimmer",
    },
)

for node in ["code_interpreter", "search_engine", "action", "knowledge", "reasoning"]:
    workflow.add_edge(node, "supervisor")

workflow.add_conditional_edges("trimmer", trimmer_router, {"aggregator": "sanitizer"})
workflow.add_edge("sanitizer", "aggregator")
workflow.add_edge("aggregator", END)

memory = MemorySaver()
supervisor_app = workflow.compile(checkpointer=memory, interrupt_before=["action"])


class Supervisor:
    def __init__(self):
        self.app = supervisor_app

    async def execute_plan(self, req):
        logger.info("Starting automated execution flow")
        yield {"type": "status", "node": "Analyzing request"}

        initial_state = {
            "req": req,
            "steps": [],
            "current_step_index": 0,
            "consolidated_results": [],
            "final_answer": "",
            "next_node": "",
            "error": "",
            "replan_count": 0,
        }

        final_results = []
        config = {
            "configurable": {"thread_id": req.session_id or str(uuid7())},
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
                    "code_interpreter",
                    "search_engine",
                    "action",
                    "knowledge",
                    "reasoning",
                ]:
                    if state_update.get("error"):
                        yield {
                            "type": "error",
                            "message": "The system encountered an issue, please try again later",
                        }
                    else:
                        yield {
                            "type": "tool_result",
                            "agent": node_name,
                            "content": state_update.get(
                                "last_agent_result", "Completed"
                            ),
                        }

                elif node_name == "aggregator":
                    yield {"type": "status", "node": "Information synthesis"}

        if not final_results:
            final_results = ["No suitable data found in the system"]

        async for chunk in response_generator.aggregate_stream(
            req.query, final_results
        ):
            yield {"type": "message", "chunk": chunk}

        pass


supervisor = Supervisor()
