import time
from typing import Any, Dict, List, Literal
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
from src.core.prompts import PromptType, prompt_registry
from src.workflow.brain import llm
from src.workflow.state import ActingState
from uuid6 import uuid7

class TaskEvaluation(BaseModel):
    status: Literal["PASS", "FAIL"] = Field(description="Operational status determining outcome success or failure")
    feedback: str = Field(description="Detailed structural feedback explaining functional operational outcome")
    revised_task: str = Field(default="", description="Revised executable task parameters provided upon validation failure")

async def supervisor_node(state: ActingState):
    start_time = state.get("start_time")
    if not start_time:
        start_time = time.time()

    if time.time() - start_time > 45:
        logger.exception("The artificial intelligence workflow execution exceeded the predefined maximum time limit")
        return {
            "next_node": "trimmer",
            "error": "The submitted request is highly complex and has exceeded the maximum processing time allowed by the system",
        }

    steps = state.get("steps", [])
    idx = state.get("current_step_index", 0)
    replan_count = state.get("replan_count", 0)

    if replan_count > 6:
        return {
            "steps": steps,
            "current_step_index": len(steps),
            "next_node": "trimmer",
            "error": "The artificial intelligence agent has exceeded the maximum allowed number of tool execution steps",
        }

    if not steps:
        steps = await planning.create_plan(state["req_data"])
        idx = 0

    if state.get("error"):
        logger.warning("The system is skipping subsequent execution steps due to a previously encountered issue")
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
    current_task = step.get("task", "")
    req_data = state.get("req_data", {})

    try:
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

            prompt_template = prompt_registry.get(PromptType.SELF_REFLECTION)
            prompt = prompt_template.format(res=res)
            
            try:
                eval_res = await evaluator_llm.ainvoke(prompt)
                if eval_res.status == "FAIL":
                    replan_count += 1
                    logger.warning("Self evaluation framework failed initiating automatic structural replanning module")
                    current_task = eval_res.revised_task or current_task
                    final_res = res
                else:
                    final_res = res
                    break
            except Exception:
                logger.debug("Evaluation structural parsing failed accepting current returned execution result securely")
                final_res = res
                break

        if replan_count >= 3:
            final_res = "The agent was unable to successfully complete the designated operational task"

        return {
            "current_step_index": idx + 1,
            "consolidated_results": [f"[{agent_name} - Step {idx+1}]:\n{final_res}"],
            "last_agent_result": final_res,
        }
    except Exception:
        logger.exception("The internal execution node routing component encountered an unexpected catastrophic failure")
        return {
            "consolidated_results": ["The execution step failed completely"],
            "error": "The system encountered an unexpected error and requires you to try again later",
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
        logger.info("Summarizing lengthy execution results optimizing overall structural memory context window")
        try:
            combined = "\n\n".join(str(r) for r in results)
            summary_prompt = f"Summarize concisely preserving facts IDs data:\n\n{combined[:20000]}"
            summary_res = await llm.ainvoke(summary_prompt)
            trimmed = summary_res.content.strip()
        except Exception:
            logger.exception("Contextual summary generation failed executing default hard string truncation algorithm")
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

    async def execute_plan(self, req_data):
        logger.info("Initialized operational execution flow establishing secure logical routing processing sequence")
        yield {"type": "status", "node": "The system is analyzing your request processing internal algorithmic pathways"}

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
                elif node_name in ["code_interpreter", "search_engine", "action", "knowledge", "reasoning"]:
                    if state_update.get("error"):
                        yield {"type": "error", "message": "The system encountered an internal execution issue processing specific node"}
                    else:
                        yield {"type": "tool_result", "agent": node_name, "content": state_update.get("last_agent_result", "Completed")}

                elif node_name == "aggregator":
                    yield {"type": "status", "node": "Synthesizing retrieved information assembling comprehensive structural analytical network response"}

        if not final_results:
            final_results = ["Unable to successfully locate required data fulfilling specific internal processing criteria"]

        query = req_data.get("query", "")
        async for chunk in response_generator.aggregate_stream(query, final_results):
            yield {"type": "message", "chunk": chunk}

supervisor = Supervisor()