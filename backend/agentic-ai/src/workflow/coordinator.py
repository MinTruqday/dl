import time
from langgraph.types import Send
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from loguru import logger

from src.workflow.brain import brain
from src.agents.code_interpreter import code_interpreter_agent
from src.tools.search_engine import search_engine_agent
from src.workflow.dispatcher import dispatcher
from src.agents.draft_generator import draft_generator_agent
from src.agents.knowledge import knowledge_agent
from src.agents.reasoning import reasoning_agent
from src.workflow.aggregator import aggregator_agent
from uuid6 import uuid7

from src.workflow.state import CoordinatorState

async def supervisor_node(state: CoordinatorState):
    start_time = state.get("start_time")
    if not start_time:
        start_time = time.time()
        
    if time.time() - start_time > 45:
        logger.error("Execution exceeded 45 seconds budget.")
        return {"next_node": "aggregator", "error": "Yêu cầu quá phức tạp, đã vượt quá ngân sách thời gian xử lý (45s)"}

    steps = state.get("steps", [])
    idx = state.get("current_step_index", 0)
    replan_count = state.get("replan_count", 0)
    
    if replan_count > 6:
        return {"steps": steps, "current_step_index": len(steps), "next_node": "aggregator", "error": "Tool budget exceeded"}
        
    if not steps:
        steps = await brain.create_plan(state["req"])
        idx = 0
        
    if state.get("error"):
        logger.warning(f"Coordinator: Skipping further tools due to error: {state.get('error')}")
        return {"steps": steps, "current_step_index": len(steps), "next_node": "aggregator", "start_time": start_time}
        
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
        from src.workflow.brain import llm
        
        replan_count = 0
        final_res = ""
        while replan_count < 3:
            if agent_name == "ToolDispatcher":
                token = getattr(req, "token", None)
                res = await tool_callable.execute(task_desc, {}, req.user_id, token)
            elif agent_name == "KnowledgeAgent":
                res = await tool_callable.execute(req)
            else:
                res = await tool_callable.execute(task_desc)
            
            prompt = f"Analyze if this execution result is a technical failure (e.g. stacktrace, obvious unhandled error, markdown formatting failure). Output 'FAIL' if it's broken, otherwise 'PASS'.\n\nResult:\n{res}"
            eval_res = await llm.ainvoke(prompt)
            
            if "FAIL" in eval_res.content.upper():
                replan_count += 1
                logger.warning(f"Self-reflection failed for {agent_name}, retrying {replan_count}/3")
                final_res = res
            else:
                final_res = res
                break
                
        if replan_count >= 3:
            final_res = f"Không thể thực thi tác vụ này sau 3 lần thử. Trả về lỗi:\n{final_res}"
            
        return {
            "consolidated_results": [f"Step {idx+1} result ({agent_name}):\n{final_res}"],
            "last_agent_result": final_res
        }
    except Exception as e:
        logger.error(f"Coordinator: Node execution failed: {e}")
        return {
            "consolidated_results": [f"Error at step {idx+1} ({agent_name}): {str(e)}"],
            "error": str(e)
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



async def trimmer_node(state: CoordinatorState):
    results = state.get("consolidated_results", [])
    if not results:
        return {"next_node": "aggregator"}
        
    total_length = sum(len(str(r)) for r in results)
    if total_length > 10000:
        logger.info(f"Trimming consolidated results (Length: {total_length})")
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=0)
        combined = "\n\n".join(results)
        chunks = splitter.split_text(combined)
        trimmed = chunks[0] + "\n[Nội dung đã được cắt bớt do quá dài]" if chunks else combined
        return {"consolidated_results": [trimmed], "next_node": "aggregator"}
        
    return {"next_node": "aggregator"}

def trimmer_router(state: CoordinatorState):
    return state.get("next_node", "aggregator")

async def sanitizer_node(state: CoordinatorState):
    req = state.get("req")
    if req:
        if hasattr(req, "token"): req.token = None
        if hasattr(req, "user_id"): req.user_id = None
        if hasattr(req, "session_id"): req.session_id = None
    return {"req": req, "next_node": "aggregator"}

async def aggregator_node(state: CoordinatorState):
    return {"final_answer": ""}

def router(state: CoordinatorState):
    steps = state.get("steps", [])
    if not steps:
        return "supervisor"
    if state.get("consolidated_results"):
        return "trimmer"
        
    sends = []
    for idx, step in enumerate(steps):
        agent_name = step.get("agent", "ToolDispatcher")
        route_map = {
            "CodeInterpreter": "code_interpreter",
            "SearchEngine": "search_engine",
            "ToolDispatcher": "action_agent",
            "InternalAPI": "action_agent",
            "DraftGenerator": "draft_generator",
            "KnowledgeAgent": "knowledge_agent",
            "ReasoningAgent": "reasoning_agent"
        }
        target = route_map.get(agent_name, "action_agent")
        sends.append(Send(target, {"req": state["req"], "steps": steps, "current_step_index": idx}))
    
    return sends

workflow = StateGraph(CoordinatorState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("code_interpreter", code_interpreter_node)
workflow.add_node("search_engine", search_engine_node)
workflow.add_node("action_agent", action_agent_node)
workflow.add_node("draft_generator", draft_generator_node)
workflow.add_node("knowledge_agent", knowledge_agent_node)
workflow.add_node("reasoning_agent", reasoning_agent_node)
workflow.add_node("trimmer", trimmer_node)
workflow.add_node("sanitizer", sanitizer_node)
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
    workflow.add_edge(node, "trimmer")

workflow.add_conditional_edges("trimmer", trimmer_router, {"aggregator": "sanitizer"})
workflow.add_edge("sanitizer", "aggregator")
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
