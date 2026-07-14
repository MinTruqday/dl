import time
from typing import Any, Dict, List, Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from loguru import logger
from pydantic import BaseModel, Field
from src.agents.acting import actor
from src.agents.interpreter import interpreter
from src.agents.planning import planner
from src.agents.reasoning import reasoner
from src.agents.analysis import researcher
from src.agents.generation import response_generator
from src.agents.engine import search_engine
from src.workflow.state import ActingState
from uuid6 import uuid7

from src.schemas.evaluation import TaskEvaluation

async def supervisor_node(state: ActingState):
    start_time = state.get("start_time")
    if not start_time:
        start_time = time.time()

    if time.time() - start_time > 45:
        logger.exception("AI task execution exceeded hard timeout")
        return {
            "next_nodes": ["trimmer"],
            "error": "Hệ thống đã tự động dừng tiến trình do vượt quá thời gian xử lý cho phép",
        }

    steps = state.get("steps", [])
    idx = state.get("current_step_index", 0)
    replan_count = state.get("replan_count", 0)

    if replan_count > 6:
        return {
            "steps": steps,
            "current_step_index": len(steps),
            "next_nodes": ["trimmer"],
            "error": "Tiến trình bị hủy do vượt quá giới hạn số bước lập kế hoạch",
        }

    if not steps:
        steps = await planner.create_plan(state["req_data"])
        from src.agents.routing import plan_validator
        steps = plan_validator.validate_plan(steps)
        idx = 0

    if state.get("error"):
        logger.warning("Skipping subsequent plan steps due to previous node error")
        return {
            "steps": steps,
            "current_step_index": len(steps),
            "next_nodes": ["trimmer"],
            "start_time": start_time,
        }

    if idx >= len(steps):
        return {"steps": steps, "current_step_index": idx, "next_nodes": ["trimmer"]}

    current_group = steps[idx]
    
    route_map = {
        "InterpreterAgent": "interpreter",
        "EngineAgent": "search_engine",
        "Action": "action",
        "Knowledge": "knowledge",
        "Reasoning": "reasoning",
        "SwarmAgent": "swarm",
        "MCTSAgent": "mcts"
    }

    next_nodes = list(set([route_map.get(s.get("agent", "Action"), "action") for s in current_group]))
    return {"steps": steps, "current_step_index": idx, "next_nodes": next_nodes}

async def execute_tool_node(state: ActingState, tool_callable, agent_name: str):
    import asyncio
    import re
    idx = state.get("current_step_index", 0)
    steps = state.get("steps", [])

    if idx >= len(steps):
        return {"current_step_index": idx + 1}

    current_group = steps[idx]
    my_tasks = [s for s in current_group if s.get("agent", "Action") == agent_name]
    req_data = state.get("req_data", {})

    def _extract_code_block(text: str) -> str:
        match = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    async def _exec_task(task_obj):
        current_task = task_obj.get("task", "")
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

                code_block = _extract_code_block(str(res))
                if code_block and agent_name in ("InterpreterAgent", "Action"):
                    from src.harness.sandbox import CodeSandbox
                    sandbox = CodeSandbox(use_docker=False)
                    sandbox_retry = 0
                    while sandbox_retry < 2:
                        success, stdout, stderr = sandbox.execute_code(code_block)
                        if success:
                            res = f"{res}\n\n[Sandbox Output]\n{stdout.strip()}"
                            break
                        else:
                            sandbox_retry += 1
                            if sandbox_retry < 2:
                                current_task = f"{current_task}\n\n[Previous code failed with error]\n{stderr}\nFix the code and retry."
                                if agent_name == "Action":
                                    res = await tool_callable.execute(current_task, {}, req_data.get("user_id"), req_data.get("token"))
                                else:
                                    res = await tool_callable.execute(current_task)
                                code_block = _extract_code_block(str(res))
                            else:
                                res = f"{res}\n\n[Sandbox Error]\n{stderr.strip()}"
                    sandbox.cleanup()

                from src.core.registry import PromptType, registry

                prompt_template = registry.get(PromptType.SELF_REFLECTION)
                prompt = prompt_template.format(res=res)

                try:
                    eval_res = await evaluator_llm.ainvoke(prompt)

                    if eval_res.status == "FAIL":
                        replan_count += 1
                        logger.warning("Self-reflection failed, initiating replan sequence")
                        current_task = eval_res.revised_task or current_task
                        final_res = res
                    else:
                        final_res = res
                        break
                except Exception:
                    logger.exception("Evaluation result parsing error")
                    final_res = res
                    break

            if replan_count >= 3:
                final_res = "The agent was unable to complete the task"
            return final_res

        except Exception:
            logger.exception("Execution server internal error")
            return "The execution step failed"

    task_results = await asyncio.gather(*[_exec_task(t) for t in my_tasks])

    return {
        "current_step_index": idx + 1,
        "consolidated_results": [f"[{agent_name} - Step {idx+1}]:\n{res}" for res in task_results],
        "last_agent_result": task_results[-1] if task_results else "Completed",
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
    return await execute_tool_node(state, reasoner, "Reasoning")

async def swarm_node(state: ActingState):
    idx = state.get("current_step_index", 0)
    steps = state.get("steps", [])

    if idx >= len(steps):
        return {"current_step_index": idx + 1}

    current_group = steps[idx]
    my_tasks = [s for s in current_group if s.get("agent", "Action") == "SwarmAgent"]
    
    from src.workflow.graph import llm
    from src.agents.swarm import create_swarm_workflow
    from src.agents.specialized.coder import CoderAgent
    from src.agents.specialized.reviewer import ReviewerAgent
    from src.agents.specialized.secops import SecOpsAgent
    import asyncio
    
    specialized_agents = {
        "coder": CoderAgent(llm),
        "reviewer": ReviewerAgent(llm),
        "secops": SecOpsAgent(llm)
    }
    swarm_app = create_swarm_workflow(llm, specialized_agents)
    
    async def _run_swarm(task_obj):
        current_task = task_obj.get("task", "")
        init_state = {
            "task": current_task,
            "is_complete": False,
            "current_agent": "supervisor",
            "messages": [],
            "artifacts": {}
        }
        final_artifacts = {}
        final_messages = []

        async for output in swarm_app.astream(init_state, {"recursion_limit": 15}):
            for node_name, state_update in output.items():
                if "artifacts" in state_update:
                    final_artifacts.update(state_update["artifacts"])
                if "messages" in state_update:
                    final_messages = state_update["messages"]

        parts = []
        if final_artifacts.get("code"):
            parts.append(f"[Generated Code]\n{final_artifacts['code']}")
        if final_artifacts.get("review"):
            parts.append(f"[Code Review]\n{final_artifacts['review']}")
        if final_artifacts.get("security_report"):
            parts.append(f"[Security Report]\n{final_artifacts['security_report']}")
        if not parts and final_messages:
            parts = [msg.content for msg in final_messages if hasattr(msg, "content")]

        return "\n\n".join(parts) if parts else "Swarm produced no output"

    task_results = await asyncio.gather(*[_run_swarm(t) for t in my_tasks])
    
    return {
        "current_step_index": idx + 1,
        "consolidated_results": [f"[SwarmAgent - Step {idx+1}]:\n{res}" for res in task_results],
        "last_agent_result": task_results[-1] if task_results else "Completed",
    }

async def mcts_node(state: ActingState):
    idx = state.get("current_step_index", 0)
    steps = state.get("steps", [])

    if idx >= len(steps):
        return {"current_step_index": idx + 1}

    current_group = steps[idx]
    my_tasks = [s for s in current_group if s.get("agent", "Action") == "MCTSAgent"]
    
    from src.workflow.graph import llm
    from src.agents.mcts import MCTSGenerator
    import asyncio
    
    mcts_agent = MCTSGenerator(llm=llm, evaluator_llm=llm, max_iterations=3)
    
    async def _run_mcts(task_obj):
        current_task = task_obj.get("task", "")
        init_state = {"task": current_task, "code": "", "approach": ""}
        best_state = await mcts_agent.search(init_state)
        return f"MCTS approach '{best_state.get('approach', '')}' produced code:\n{best_state.get('code', '')}"

    task_results = await asyncio.gather(*[_run_mcts(t) for t in my_tasks])
    
    return {
        "current_step_index": idx + 1,
        "consolidated_results": [f"[MCTSAgent - Step {idx+1}]:\n{res}" for res in task_results],
        "last_agent_result": task_results[-1] if task_results else "Completed",
    }

async def trimmer_node(state: ActingState):
    results = state.get("consolidated_results", [])
    if not results:
        return {"next_nodes": ["aggregator"]}

    total_length = sum(len(str(r)) for r in results)
    if total_length > 12000:
        logger.info("Aggregating and consolidating node results")
        try:
            from src.workflow.graph import llm

            combined = "\n\n".join(str(r) for r in results)
            from src.core.registry import registry, PromptType
            summary_prompt = registry.get(PromptType.ORCHESTRATOR_TRIMMER).format(
                combined=combined[:20000]
            )
            summary_res = await llm.ainvoke(summary_prompt)
            trimmed = summary_res.content.strip()
        except Exception as e:
            logger.exception("Summary trimmer execution error")
            trimmed = "\n\n".join(str(r) for r in results)[:12000]
        return {"consolidated_results": [trimmed], "next_nodes": ["aggregator"]}

    return {"next_nodes": ["aggregator"]}

def trimmer_router(state: ActingState):
    return state.get("next_nodes", ["aggregator"])

async def sanitizer_node(state: ActingState):
    from src.core.security.governance import enforce_resource_limits, sanitize_output
    from loguru import logger
    
    results = state.get("consolidated_results", [])
    if not results:
        return {"next_nodes": ["aggregator"]}
        
    is_valid, error_msg = enforce_resource_limits(results)
    if not is_valid:
        logger.warning(f"Governance enforcement failed: {error_msg}")
        return {
            "error": "Phát hiện rủi ro an toàn tài nguyên. Tiến trình bị hệ thống bảo mật tự động ngắt kết nối.",
            "next_nodes": ["aggregator"]
        }
        
    sanitized_results = sanitize_output(results)
    return {"consolidated_results": sanitized_results, "next_nodes": ["aggregator"]}

async def aggregator_node(state: ActingState):
    return {"final_answer": ""}

def router(state: ActingState):
    return state.get("next_nodes", ["aggregator"])

workflow = StateGraph(ActingState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("interpreter", code_interpreter_node)
workflow.add_node("search_engine", search_engine_node)
workflow.add_node("action", actor_agent_node)
workflow.add_node("knowledge", researcher_agent_node)
workflow.add_node("reasoning", reasoner_agent_node)
workflow.add_node("swarm", swarm_node)
workflow.add_node("mcts", mcts_node)
workflow.add_node("trimmer", trimmer_node)
workflow.add_node("sanitizer", sanitizer_node)
workflow.add_node("aggregator", aggregator_node)

workflow.set_entry_point("supervisor")

workflow.add_conditional_edges(
    "supervisor",
    router,
    {n: n for n in workflow.nodes.keys() if n not in ["supervisor", "sanitizer"]},
)

for node in workflow.nodes.keys():
    if node not in ["supervisor", "aggregator", "trimmer", "sanitizer"]:
        workflow.add_edge(node, "supervisor")

workflow.add_conditional_edges("trimmer", trimmer_router, {"aggregator": "sanitizer"})
workflow.add_edge("sanitizer", "aggregator")
workflow.add_edge("aggregator", END)

memory = MemorySaver()
supervisor_app = workflow.compile(checkpointer=memory, interrupt_before=["action"])

class OrchestrationWorkflow:
    """
    <module_purpose>
    <purpose>Orchestrates the continuous event loop for the Metis main reasoning graph.</purpose>
    <metis_behavior>Streams events strictly in real-time. Yields formalized JSON outputs and suppresses internal stack traces.</metis_behavior>
    </module_purpose>
    """
    def __init__(self):
        self.app = supervisor_app

    async def execute_plan(self, req_data):
        from src.memory.global_state import global_state
        logger.info("Initializing orchestration execution stream")
        yield {"type": "status", "node": "Hệ thống đang tiến hành phân tích yêu cầu"}

        session_id = req_data.get("session_id", str(uuid7()))

        project_context = await global_state.get_project_context_async(session_id)
        if project_context:
            req_data["global_context"] = project_context

        recent_episodes = await global_state.get_recent_episodes(k=3)
        if recent_episodes:
            req_data["episodic_context"] = "\n---\n".join(recent_episodes)

        initial_state = {
            "req_data": req_data,
            "steps": req_data.get("plan", []),
            "current_step_index": 0,
            "consolidated_results": [],
            "final_answer": "",
            "next_nodes": [],
            "error": "",
            "replan_count": 0,
        }

        final_results = []
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
                    "swarm",
                    "mcts",
                ]:
                    if not state_update.get("error"):
                        yield {
                            "type": "tool_result",
                            "agent": node_name,
                            "content": state_update.get("last_agent_result", "Completed"),
                        }

                elif node_name == "aggregator":
                    yield {"type": "status", "node": "Hệ thống đang tổng hợp dữ liệu phản hồi"}

        if not final_results:
            final_results = ["Unable to locate data"]

        query = req_data.get("query", "")
        full_response_chunks = []
        async for chunk in response_generator.aggregate_stream(query, final_results):
            full_response_chunks.append(chunk.get("chunk", "") if isinstance(chunk, dict) else str(chunk))
            yield {"type": "message", "chunk": chunk}

        try:
            combined = " ".join(full_response_chunks)
            if combined.strip():
                await global_state.add_episodic_memory(
                    session_id=session_id,
                    summary=f"Query: {query[:200]}\nResponse summary: {combined[:500]}",
                )
        except Exception:
            logger.exception("Episodic memory storage failed")

supervisor = OrchestrationWorkflow()
