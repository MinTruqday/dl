from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from loguru import logger

from src.core.brain import brain
from src.agents.code_interpreter import code_interpreter_agent
from src.integrations.search_engine import search_engine_agent
from src.tools.internal_api import internal_api_agent
from src.agents.draft_generator import draft_generator_agent
from src.agents.knowledge import knowledge_agent
from src.agents.reasoning import reasoning_agent
from src.core.aggregator import aggregator_agent

from src.models.state import CoordinatorState

async def supervisor_node(state: CoordinatorState):
    steps = state.get("steps", [])
    idx = state.get("current_step_index", 0)
    replan_count = state.get("replan_count", 0)
    
    if replan_count > 3:
        return {"steps": steps, "current_step_index": len(steps), "next_node": "aggregator", "error": "Tool budget exceeded"}
        
    if not steps or (state.get("error") and replan_count <= 3):
        if state.get("error"):
            req = state["req"]
            req.context = f"Previous error: {state['error']}. Please use a different approach."
            steps = await brain.create_plan(req)
            idx = 0
            return {"steps": steps, "current_step_index": idx, "replan_count": replan_count + 1, "error": ""}
        else:
            steps = await brain.create_plan(state["req"])
            idx = 0
        
    if idx >= len(steps):
        return {"steps": steps, "current_step_index": idx, "next_node": "aggregator"}
        
    current_step = steps[idx]
    agent_name = current_step.get("agent", "ActionAgent")
    
    route_map = {
        "CodeInterpreter": "code_interpreter",
        "SearchEngine": "search_engine",
        "ActionAgent": "action_agent",
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
        if agent_name == "ActionAgent":
            if any(keyword in task_desc.lower() for keyword in ["xoá", "xóa", "delete", "remove", "drop"]):
                if not getattr(req, "useSmart", False):
                    res = "Hành động này được phân loại là NGUY HIỂM. Hệ thống đang chờ phê duyệt từ người dùng (Human-in-the-loop)."
                    return {
                        "consolidated_results": state.get("consolidated_results", []) + [res],
                        "current_step_index": idx + 1,
                        "last_agent_result": res
                    }
                    
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
    return await execute_tool_node(state, internal_api_agent, "ActionAgent")

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
coordinator_app = workflow.compile()

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
        async for output in self.app.astream(initial_state):
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
