from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from loguru import logger

from src.core.brain import brain
from src.agents.code_interpreter import code_interpreter_agent
from src.integrations.search_engine import search_engine_agent
from src.tools.internal_api import internal_api_agent
from src.agents.draft_generator import draft_generator_agent
from src.agents.knowledge import knowledge_agent
from src.core.aggregator import aggregator_agent

from src.models.state import CoordinatorState

async def supervisor_node(state: CoordinatorState):
    steps = state.get("steps", [])
    idx = state.get("current_step_index", 0)
    
    if not steps:
        new_steps = await brain.create_plan(state["req"])
        return {"steps": new_steps, "current_step_index": 0}
        
    if idx >= len(steps):
        return {"next_node": "aggregator"}
        
    current_step = steps[idx]
    agent_name = current_step.get("agent", "ActionAgent")
    
    route_map = {
        "CodeInterpreter": "code_interpreter",
        "SearchEngine": "search_engine",
        "ActionAgent": "action_agent",
        "InternalAPI": "action_agent",
        "DraftGenerator": "draft_generator",
        "KnowledgeAgent": "knowledge_agent"
    }
    
    next_node = route_map.get(agent_name, "action_agent")
    return {"next_node": next_node}

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
            res = await tool_callable.execute(task_desc, {}, req.user_id)
        elif agent_name == "KnowledgeAgent":
            res = await tool_callable.execute(req)
        else:
            res = await tool_callable.execute(task_desc)
            
        current_results = state.get("consolidated_results", [])
        return {
            "consolidated_results": current_results + [f"Kết quả bước {idx+1} ({agent_name}):\n{res}"],
            "current_step_index": idx + 1
        }
    except Exception as e:
        logger.error(f"Coordinator: Node execution failed: {e}")
        current_results = state.get("consolidated_results", [])
        return {
            "consolidated_results": current_results + ["Hệ thống đang gặp sự cố, vui lòng thử lại sau."],
            "current_step_index": idx + 1,
            "error": str(e)
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

async def aggregator_node(state: CoordinatorState):
    req = state.get("req")
    results = state.get("consolidated_results", [])
    final_answer = await aggregator_agent.aggregate(req.query, results)
    return {"final_answer": final_answer}

def router(state: CoordinatorState):
    return state.get("next_node", "aggregator")

workflow = StateGraph(CoordinatorState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("code_interpreter", code_interpreter_node)
workflow.add_node("search_engine", search_engine_node)
workflow.add_node("action_agent", action_agent_node)
workflow.add_node("draft_generator", draft_generator_node)
workflow.add_node("knowledge_agent", knowledge_agent_node)
workflow.add_node("aggregator", aggregator_node)

workflow.set_entry_point("supervisor")

workflow.add_conditional_edges("supervisor", router, {
    "code_interpreter": "code_interpreter",
    "search_engine": "search_engine",
    "action_agent": "action_agent",
    "draft_generator": "draft_generator",
    "knowledge_agent": "knowledge_agent",
    "aggregator": "aggregator"
})

for node in ["code_interpreter", "search_engine", "action_agent", "draft_generator", "knowledge_agent"]:
    workflow.add_edge(node, "supervisor")

workflow.add_edge("aggregator", END)
coordinator_app = workflow.compile()

class CoordinatorAgent:
    def __init__(self):
        self.app = coordinator_app

    async def execute_plan(self, req):
        logger.info("Coordinator: Starting LangGraph execution flow")
        yield {"type": "status", "node": "Lập kế hoạch phân rã tác vụ (Brain)"}
        
        initial_state = {
            "req": req,
            "steps": [],
            "current_step_index": 0,
            "consolidated_results": [],
            "final_answer": "",
            "next_node": "",
            "error": ""
        }
        
        async for output in self.app.astream(initial_state):
            for node_name, state_update in output.items():
                if node_name == "supervisor":
                    steps = state_update.get("steps")
                    if steps and state_update.get("current_step_index") == 0:
                        yield {"type": "plan", "steps": steps}
                elif node_name in ["code_interpreter", "search_engine", "action_agent", "draft_generator", "knowledge_agent"]:
                    if state_update.get("error"):
                        yield {"type": "error", "message": "Hệ thống đang gặp sự cố, vui lòng thử lại sau."}
                    else:
                        yield {"type": "tool_result", "agent": node_name, "content": "Đã xử lý xong tác vụ."}
                        
                elif node_name == "aggregator":
                    yield {"type": "status", "node": "Tổng hợp kết quả (Aggregator)"}
                    if "final_answer" in state_update:
                        yield {"type": "message", "chunk": state_update["final_answer"]}
                        
        pass
coordinator = CoordinatorAgent()
