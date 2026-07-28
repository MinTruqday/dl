import json
import time

from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient
from langgraph.graph import END, StateGraph
from loguru import logger
from src.core.infrastructure.configuration import settings
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

    if time.time() - start_time > settings.AGENT_EXECUTION_TIMEOUT_SECONDS:
        logger.warning("AI task execution exceeded hard timeout")
        return {
            "next_nodes": ["trimmer"],
            "error": "execution_timeout",
        }

    steps = state.get("steps", [])
    completed_tasks = state.get("completed_tasks", [])
    task_status = state.get("task_status", {})
    replan_count = state.get("replan_count", 0)
    dynamic_injections = state.get("dynamic_injections", [])

    if replan_count > 6:
        return {
            "next_nodes": ["trimmer"],
            "error": "planning_limit_exceeded",
        }

    if not steps:
        nodes = await planner.create_plan(state["req_data"])
        from src.agents.routing import plan_validator
        nodes = await plan_validator.validate_plan(nodes)
        
        steps = nodes
        task_status = {n["id"]: "pending" for n in steps}
        completed_tasks = []

    req_data = state.get("req_data", {})
    session_id = req_data.get("session_id", "")
    if session_id:
        from src.harness.governance import governance

        session_summary = governance.get_session_summary(session_id)
        if session_summary:
            plan_decision = governance.check_plan_steps(session_id, len(steps))
            if not plan_decision.allowed:
                return {
                    "steps": steps,
                    "task_status": task_status,
                    "completed_tasks": completed_tasks,
                    "next_nodes": ["trimmer"],
                    "error": "plan_policy_denied",
                }

    if dynamic_injections:
        for new_node in dynamic_injections:
            if new_node["id"] not in task_status:
                steps.append(new_node)
                task_status[new_node["id"]] = "pending"
        dynamic_injections = []

    if state.get("error"):
        logger.warning("Skipping subsequent plan steps due to previous node error")
        return {
            "steps": steps,
            "next_nodes": ["trimmer"],
            "start_time": start_time,
        }

    ready_tasks = []
    for n in steps:
        if task_status.get(n["id"]) == "pending":
            deps = n.get("dependencies", [])
            if all(dep in completed_tasks for dep in deps):
                if session_id:
                    from src.harness.governance import governance

                    session_summary = governance.get_session_summary(session_id)
                    decision = governance.check_tool_allowed(
                        session_id,
                        n.get("agent", "Action"),
                    )
                    if session_summary and not decision.allowed:
                        task_status[n["id"]] = "failed"
                        continue
                ready_tasks.append(n)
                task_status[n["id"]] = "running"
    
    if not ready_tasks:
        if all(status == "completed" for status in task_status.values()):
            return {"steps": steps, "task_status": task_status, "completed_tasks": completed_tasks, "next_nodes": ["trimmer"]}
        if any(status == "failed" for status in task_status.values()):
            return {
                "steps": steps,
                "task_status": task_status,
                "completed_tasks": completed_tasks,
                "next_nodes": ["trimmer"],
                "error": "task_execution_failed",
            }
        else:
            is_running = any(status == "running" for status in task_status.values())
            if not is_running:
                logger.error("DAG Deadlock detected!")
                return {"next_nodes": ["trimmer"], "error": "dag_deadlock"}
            return {"steps": steps, "task_status": task_status, "next_nodes": []}

    execution_history = state.get("execution_history", [])
    current_sig = tuple(sorted([t["id"] for t in ready_tasks]))
    execution_history.append(current_sig)
    if len(execution_history) >= 3 and execution_history[-1] == execution_history[-2] == execution_history[-3]:
        logger.warning("Infinite loop detected in supervisor execution")
        return {
            "next_nodes": ["trimmer"],
            "error": "infinite_loop_detected",
            "execution_history": execution_history,
        }

    route_map = {
        "InterpreterAgent": "interpreter",
        "EngineAgent": "search_engine",
        "Action": "action",
        "Knowledge": "knowledge",
        "Reasoning": "reasoning",
        "SwarmAgent": "swarm",
        "MCTSAgent": "mcts",
        "SpawnerAgent": "spawner",
    }

    next_nodes = list(set([route_map.get(s.get("agent", "Action"), "action") for s in ready_tasks]))
    
    return {
        "steps": steps, 
        "task_status": task_status,
        "completed_tasks": completed_tasks,
        "current_step_index": len(completed_tasks),
        "next_nodes": next_nodes,
        "dynamic_injections": dynamic_injections,
        "execution_history": execution_history,
        "start_time": start_time,
    }

async def execute_tool_node(state: ActingState, tool_callable, agent_name: str):
    import asyncio
    
    steps = state.get("steps", [])
    task_status = state.get("task_status", {})
    completed_tasks = state.get("completed_tasks", [])

    my_tasks = [s for s in steps if task_status.get(s["id"]) == "running" and s.get("agent", "Action") == agent_name]
    if not my_tasks:
        return {}

    req_data = state.get("req_data", {})
    session_id = req_data.get("session_id", "")
    memory_context = None
    if (
        settings.AGENT_PROACTIVE_MEMORY_ENABLED
        and session_id
        and agent_name not in {"Knowledge"}
    ):
        from src.proactive.middleware import memory_middleware

        trajectory = [
            {"role": "assistant", "content": str(item)}
            for item in state.get("consolidated_results", [])
        ]
        memory_context = await memory_middleware.process(
            session_id=session_id,
            trajectory=trajectory,
            step_count=len(completed_tasks) + 1,
            task_description="\n".join(
                str(task.get("task", "")) for task in my_tasks
            ),
            user_id=str(req_data.get("user_id", "")),
        )

    async def _exec_task(task_obj):
        current_task = task_obj.get("task", "")
        if memory_context:
            current_task = f"{current_task}\n\n{memory_context}"
        try:
            if session_id:
                from src.harness.governance import governance

                if governance.get_session_summary(session_id):
                    governance.record_tool_call(session_id, current_task)
            from src.workflow.graph import llm
            evaluator_llm = llm.with_structured_output(TaskEvaluation)

            replan_count = 0
            final_res = ""

            while replan_count < 3:
                if agent_name == "Action":
                    token = req_data.get("token")
                    user_id = req_data.get("user_id")
                    res = await tool_callable.execute(
                        current_task,
                        {},
                        user_id,
                        token,
                        auto_approve=bool(req_data.get("approve_tools", False)),
                        session_id=session_id,
                        approval_id=req_data.get("approval_id"),
                    )
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
                        logger.warning("Self-reflection failed, initiating replan sequence")
                        try:
                            from src.memory.memo import memo_manager
                            from src.utils.background import create_background_task
                            user_id = req_data.get("user_id", "guest")
                            mem_data = [
                                {"role": "system", "content": "I attempted a task but failed. I must learn from this mistake for future reasoning."},
                                {"role": "user", "content": f"Task: {current_task}\nFailed Output: {res}\nFeedback: {eval_res.feedback}\nRevised Task for next time: {eval_res.revised_task}"}
                            ]
                            create_background_task(
                                memo_manager.add_memory(mem_data, user_id),
                                f"procedural-memory-{user_id}",
                            )
                        except Exception:
                            logger.exception("Failed to inject procedural memory")
                        current_task = eval_res.revised_task or current_task
                        final_res = res
                    else:
                        final_res = res
                        break
                except Exception:
                    logger.exception("Evaluation result parsing error")
                    final_res = json.dumps(
                        {"status": "task_evaluation_failed"}
                    )
                    break

            if replan_count >= 3:
                final_res = json.dumps({"status": "task_execution_failed"})
            return final_res

        except Exception:
            logger.exception("Execution server internal error")
            return json.dumps({"status": "execution_step_failed"})

    task_results = await asyncio.gather(*[_exec_task(t) for t in my_tasks])

    for task, result in zip(my_tasks, task_results):
        succeeded = _result_succeeded(result)
        task_status[task["id"]] = "completed" if succeeded else "failed"
        if succeeded and task["id"] not in completed_tasks:
            completed_tasks.append(task["id"])

    return {
        "task_status": task_status,
        "completed_tasks": completed_tasks,
        "consolidated_results": [f"[{agent_name} - {t['id']}]:\n{res}" for t, res in zip(my_tasks, task_results)],
        "last_agent_result": task_results[-1] if task_results else json.dumps({"status": "completed"}),
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


def _result_succeeded(result):
    try:
        payload = json.loads(result)
    except (TypeError, json.JSONDecodeError):
        return True
    if not isinstance(payload, dict) or "status" not in payload:
        return True
    return payload["status"] in {"success", "completed"}

async def swarm_node(state: ActingState):
    steps = state.get("steps", [])
    task_status = state.get("task_status", {})
    completed_tasks = state.get("completed_tasks", [])

    my_tasks = [s for s in steps if task_status.get(s["id"]) == "running" and s.get("agent", "Action") == "SwarmAgent"]
    if not my_tasks:
        return {}
    
    from src.workflow.graph import llm
    from src.agents.swarm import create_swarm_workflow
    from src.agents.coder import CoderAgent
    from src.agents.reviewer import ReviewerAgent
    from src.agents.secops import SecOpsAgent
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

        from langgraph.errors import GraphRecursionError
        from langchain_core.messages import AIMessage
        try:
            async for output in swarm_app.astream(init_state, {"recursion_limit": 15}):
                for node_name, state_update in output.items():
                    if "artifacts" in state_update:
                        final_artifacts.update(state_update["artifacts"])
                    if "messages" in state_update:
                        final_messages = state_update["messages"]
        except GraphRecursionError:
            logger.warning("Swarm recursion limit reached. Halting swarm execution")
            final_messages.append(AIMessage(content=json.dumps({"status": "recursion_limit_reached"})))

        messages = [
            msg.content
            for msg in final_messages
            if hasattr(msg, "content")
        ]
        return json.dumps(
            {
                "status": (
                    "success"
                    if final_artifacts.get("review_approved") is True
                    and final_artifacts.get("security_approved") is True
                    else "swarm_verification_failed"
                ),
                "artifacts": final_artifacts,
                "messages": messages,
            },
            ensure_ascii=False,
        )

    task_results = await asyncio.gather(*[_run_swarm(t) for t in my_tasks])
    
    for task, result in zip(my_tasks, task_results):
        succeeded = _result_succeeded(result)
        task_status[task["id"]] = "completed" if succeeded else "failed"
        if succeeded and task["id"] not in completed_tasks:
            completed_tasks.append(task["id"])

    return {
        "task_status": task_status,
        "completed_tasks": completed_tasks,
        "consolidated_results": [f"[SwarmAgent - {t['id']}]:\n{res}" for t, res in zip(my_tasks, task_results)],
        "last_agent_result": task_results[-1] if task_results else json.dumps({"status": "completed"}),
    }

async def mcts_node(state: ActingState):
    steps = state.get("steps", [])
    task_status = state.get("task_status", {})
    completed_tasks = state.get("completed_tasks", [])

    my_tasks = [s for s in steps if task_status.get(s["id"]) == "running" and s.get("agent", "Action") == "MCTSAgent"]
    if not my_tasks:
        return {}
    
    from src.workflow.graph import llm
    from src.agents.mcts import MCTSGenerator
    import asyncio
    
    mcts_agent = MCTSGenerator(llm=llm, evaluator_llm=llm, max_iterations=3)
    
    async def _run_mcts(task_obj):
        current_task = task_obj.get("task", "")
        init_state = {"task": current_task, "code": "", "approach": ""}
        best_state = await mcts_agent.search(init_state)
        code = best_state.get("code", "")
        return json.dumps(
            {
                "status": "success" if code.strip() else "mcts_generation_failed",
                "approach": best_state.get("approach", ""),
                "code": code,
            },
            ensure_ascii=False,
        )

    task_results = await asyncio.gather(*[_run_mcts(t) for t in my_tasks])
    
    for task, result in zip(my_tasks, task_results):
        succeeded = _result_succeeded(result)
        task_status[task["id"]] = "completed" if succeeded else "failed"
        if succeeded and task["id"] not in completed_tasks:
            completed_tasks.append(task["id"])

    return {
        "task_status": task_status,
        "completed_tasks": completed_tasks,
        "consolidated_results": [f"[MCTSAgent - {t['id']}]:\n{res}" for t, res in zip(my_tasks, task_results)],
        "last_agent_result": task_results[-1] if task_results else json.dumps({"status": "completed"}),
    }


async def spawner_node(state: ActingState):
    from src.agents.spawner import AgentSpawner
    from src.workflow.graph import llm

    class SpawnerExecutor:
        async def execute(self, task: str) -> str:
            matching_task = next(
                (
                    item
                    for item in state.get("steps", [])
                    if item.get("task") and item.get("task") in task
                ),
                {},
            )
            role = matching_task.get("specialization") or "Domain specialist"
            return await AgentSpawner(llm).spawn(role, task)

    return await execute_tool_node(state, SpawnerExecutor(), "SpawnerAgent")

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
        except Exception:
            logger.exception("Summary trimmer execution error")
            trimmed = "\n\n".join(str(r) for r in results)[:12000]
        return {
            "consolidated_results": [trimmed],
            "results_trimmed": True,
            "next_nodes": ["aggregator"],
        }

    return {"next_nodes": ["aggregator"]}

def trimmer_router(state: ActingState):
    return state.get("next_nodes", ["aggregator"])

async def sanitizer_node(state: ActingState):
    from src.core.security.governance import enforce_resource_limits, sanitize_output
    from loguru import logger
    
    results = state.get("consolidated_results", [])
    if not results:
        return {"next_nodes": ["aggregator"]}
    if state.get("results_trimmed"):
        results = results[-1:]
        
    is_valid, error_msg = enforce_resource_limits(results)
    if not is_valid:
        logger.warning(f"Governance enforcement failed: {error_msg}")
        return {
            "error": "resource_safety_limit_exceeded",
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
workflow.add_node("spawner", spawner_node)
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

class OrchestrationWorkflow:
    """
    <module_purpose>
        <purpose>Orchestrate the continuous event loop for the Metis main reasoning graph (LangGraph).</purpose>
        <context>Acts as the central nervous system, managing state transitions, agent delegation, and real-time streaming of events back to the client.</context>
    </module_purpose>
    
    <contract>
        <input>Takes an initial request data dictionary containing user_id, query, and optional token.</input>
        <output>Yields an asynchronous stream of structured dicts representing plan updates, tool results, and final synthesized answers.</output>
        <exceptions>Swallows internal agent exceptions to prevent crash cascades, returning safe localized error messages.</exceptions>
    </contract>
    """
    def __init__(self):
        self.workflow = workflow
        self.sync_client = MongoClient(settings.MONGODB_URI)
        self.checkpointer = MongoDBSaver(
            self.sync_client,
            db_name=settings.AGENTIC_AI_DB_NAME,
        )
        self.app = self.workflow.compile(checkpointer=self.checkpointer)

    async def execute_plan(self, req_data):
        from src.memory.global_state import global_state
        from src.harness.governance import governance
        from src.loop.rubric import standard_rubric_middleware
        from src.loop.verification import verification

        logger.info(f"Initializing orchestration execution stream for query length {len(req_data.get('query', ''))}")
        yield {"type": "status", "code": "analyzing_request"}

        session_id = req_data.get("session_id") or str(uuid7())
        req_data["session_id"] = session_id
        user_id = str(req_data.get("user_id", ""))
        role = str(req_data.get("role", "reader"))
        governance.open_session(session_id, user_id, role)

        project_context = await global_state.get_project_context_async(session_id)
        if project_context:
            req_data["global_context"] = project_context

        recent_episodes = await global_state.get_recent_episodes(
            k=3,
            session_id=session_id,
            user_id=user_id,
        )
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
            "results_trimmed": False,
            "start_time": time.time(),
        }

        final_results = []
        execution_id = str(uuid7())
        config = {
            "configurable": {"thread_id": f"{session_id}:{execution_id}"},
            "recursion_limit": settings.AGENT_RECURSION_LIMIT,
        }

        workflow_error = ""
        final_state = {}
        try:
            async for output in self.app.astream(initial_state, config=config):
                for node_name, state_update in output.items():
                    final_state.update(state_update)
                    if state_update.get("error"):
                        workflow_error = state_update["error"]
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
                        "spawner",
                    ]:
                        if not state_update.get("error"):
                            yield {
                                "type": "tool_result",
                                "agent": node_name,
                                "status": "completed",
                            }
                    elif node_name == "aggregator":
                        yield {"type": "status", "code": "synthesizing_response"}

            checkpoint = await self.app.aget_state(config)
            final_state = checkpoint.values
            final_results = final_state.get("consolidated_results", [])
            workflow_error = final_state.get("error", workflow_error)
            if workflow_error:
                yield {"type": "error", "code": workflow_error}
                return

            if not final_results:
                yield {"type": "error", "code": "no_supporting_data"}
                return

            query = req_data.get("query", "")
            full_response_chunks = []
            async for chunk in response_generator.aggregate_stream(query, final_results):
                full_response_chunks.append(
                    chunk.get("chunk", "") if isinstance(chunk, dict) else str(chunk)
                )

            combined = "".join(full_response_chunks)
            rubric_result = await standard_rubric_middleware.rubric.evaluate(
                combined,
                {"query": query},
            )
            verification_result = await verification.verify_task_completion(
                session_id=session_id,
                task_id="final_response",
                response=combined,
                steps=final_state.get("steps"),
                current_step_index=len(final_state.get("completed_tasks", [])),
                allow_ai_review=False,
            )
            if not rubric_result.passed or not verification_result.passed:
                yield {"type": "error", "code": "response_verification_failed"}
                return

            for content in full_response_chunks:
                yield {"type": "message", "chunk": content}

            try:
                await global_state.add_episodic_memory(
                    session_id=session_id,
                    summary=f"Query: {query[:200]}\nResponse summary: {combined[:500]}",
                    user_id=user_id,
                )
            except Exception:
                logger.exception("Episodic memory storage failed")
        finally:
            governance.close_session(session_id)

supervisor = OrchestrationWorkflow()
supervisor_app = supervisor.app
