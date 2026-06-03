from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from loguru import logger

from src.core.brain import brain
from src.agents.code_interpreter import code_interpreter_agent
from src.integrations.search_engine import search_engine_agent
from src.agents.dispatcher import dispatcher
from src.agents.draft_generator import draft_generator_agent
from src.agents.knowledge import knowledge_agent
from src.agents.reasoning import reasoning_agent
from src.core.aggregator import aggregator_agent
from uuid6 import uuid7

from src.models.state import CoordinatorState

async def supervisor_node(state: CoordinatorState):
    steps = state.get("steps", [])
    idx = state.get("current_step_index", 0)
    replan_count = state.get("replan_count", 0)
    
    if replan_count > 3:
        return {"steps": steps, "current_step_index": len(steps), "next_node": "aggregator", "error": "Tool budget exceeded"}
        
    if not steps:
        steps = await brain.create_plan(state["req"])
        idx = 0
        
    if state.get("error"):
        logger.warning(f"Coordinator: Skipping further tools due to error: {state.get('error')}")
        return {"steps": steps, "current_step_index": len(steps), "next_node": "aggregator"}
        
    if idx >= len(steps):
        return {"steps": steps, "current_step_index": idx, "next_node": "aggregator"}
        
    current_step = steps[idx]
    agent_name = current_step.get("agent", "ToolDispatcher")
    
    route_map = {
        "CodeInterpreter": "code_interpreter",
        "SearchEngine": "search_engine",
        "ToolDispatcher": "action_agent",
        "InternalAPI": "action_agent",
        "DraftGenerator": "draft_generator",
        "KnowledgeAgent": "knowledge_agent",
        "ReasoningAgent": "reasoning_agent"
    }
    
    next_node = route_map.get(agent_name, "action_agent")
    return {"steps": steps, "current_step_index": idx, "next_node": next_node}

async def execute_tool_node(state: CoordinatorState, tool_callable, agent_name: str):
    idx = state.get("current_step_index", 0)
    steps = state.get("steps", [])
    
    if idx >= len(steps):
        return {"current_step_index": idx + 1}
        
    step = steps[idx]
    task_desc = step.get("task", "")
    req = state.get("req")
    
    try:
        if agent_name == "ToolDispatcher":
            token = getattr(req, "token", None)
            res = await tool_callable.execute(task_desc, {}, req.user_id, token)
        elif agent_name == "KnowledgeAgent":
            res = await tool_callable.execute(req)
        else:
            res = await tool_callable.execute(task_desc)
            
        current_results = state.get("consolidated_results", [])
        return {
            "consolidated_results": current_results + [f"Kết quả bước {idx+1} ({agent_name}):\n{res}"],
            "current_step_index": idx + 1,
            "last_agent_result": res
        }
    except Exception as e:
        logger.error(f"Coordinator: Node execution failed: {e}")
        current_results = state.get("consolidated_results", [])
        return {
            "consolidated_results": current_results + [f"Lỗi tại bước {idx+1} ({agent_name}): {str(e)}"],
            "current_step_index": idx + 1,
            "error": str(e),
            "next_node": "supervisor"
        }

async def code_interpreter_node(state: CoordinatorState):
    return await execute_tool_node(state, code_interpreter_agent, "CodeInterpreter")

async def search_engine_node(state: CoordinatorState):
    return await execute_tool_node(state, search_engine_agent, "SearchEngine")

async def action_agent_node(state: CoordinatorState):
    return await execute_tool_node(state, dispatcher, "ToolDispatcher")

async def draft_generator_node(state: CoordinatorState):
    return await execute_tool_node(state, draft_generator_agent, "DraftGenerator")

async def knowledge_agent_node(state: CoordinatorState):
    return await execute_tool_node(state, knowledge_agent, "KnowledgeAgent")

async def reasoning_agent_node(state: CoordinatorState):
    return await execute_tool_node(state, reasoning_agent, "ReasoningAgent")

async def aggregator_node(state: CoordinatorState):
    return {"final_answer": ""}

def router(state: CoordinatorState):
    next_node = state.get("next_node")
    if not next_node:
        return "aggregator"
    return next_node

workflow = StateGraph(CoordinatorState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("code_interpreter", code_interpreter_node)
workflow.add_node("search_engine", search_engine_node)
workflow.add_node("action_agent", action_agent_node)
workflow.add_node("draft_generator", draft_generator_node)
workflow.add_node("knowledge_agent", knowledge_agent_node)
workflow.add_node("reasoning_agent", reasoning_agent_node)
workflow.add_node("aggregator", aggregator_node)

workflow.set_entry_point("supervisor")

workflow.add_conditional_edges("supervisor", router, {
    "code_interpreter": "code_interpreter",
    "search_engine": "search_engine",
    "action_agent": "action_agent",
    "draft_generator": "draft_generator",
    "knowledge_agent": "knowledge_agent",
    "reasoning_agent": "reasoning_agent",
    "aggregator": "aggregator"
})

for node in ["code_interpreter", "search_engine", "action_agent", "draft_generator", "knowledge_agent", "reasoning_agent"]:
    workflow.add_edge(node, "supervisor")

workflow.add_edge("aggregator", END)

memory = MemorySaver()
coordinator_app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["action_agent"]
)

class CoordinatorAgent:
    def __init__(self):
        self.app = coordinator_app

    async def execute_plan(self, req):
        logger.info("Coordinator: Starting LangGraph execution flow")
        yield {"type": "status", "node": "Phân tích yêu cầu"}
        
        initial_state = {
            "req": req,
            "steps": [],
            "current_step_index": 0,
            "consolidated_results": [],
            "final_answer": "",
            "next_node": "",
            "error": "",
            "replan_count": 0
        }
        
        final_results = []
        config = {"configurable": {"thread_id": req.session_id or str(uuid7())}}
        async for output in self.app.astream(initial_state, config=config):
            for node_name, state_update in output.items():
                if "consolidated_results" in state_update:
                    final_results = state_update["consolidated_results"]
                    
                if node_name == "supervisor":
                    steps = state_update.get("steps")
                    if steps and state_update.get("current_step_index") == 0:
                        yield {"type": "plan", "steps": steps}
                elif node_name in ["code_interpreter", "search_engine", "action_agent", "draft_generator", "knowledge_agent", "reasoning_agent"]:
                    if state_update.get("error"):
                        yield {"type": "error", "message": "Hệ thống đang gặp sự cố, vui lòng thử lại sau."}
                    else:
                        yield {"type": "tool_result", "agent": node_name, "content": state_update.get("last_agent_result", "Hoàn thành")}
                        
                elif node_name == "aggregator":
                    yield {"type": "status", "node": "Tổng hợp thông tin"}
        
        if not final_results:
            final_results = ["Không tìm thấy dữ liệu phù hợp trong hệ thống."]
            
        async for chunk in aggregator_agent.aggregate_stream(req.query, final_results):
            yield {"type": "message", "chunk": chunk}
                        
        pass
coordinator = CoordinatorAgent()
