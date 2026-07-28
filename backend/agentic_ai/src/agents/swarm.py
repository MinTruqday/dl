import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from loguru import logger
from src.core.registry import PromptType, registry
from src.schemas.swarm import SwarmState, SwarmRouteDecision

class SupervisorAgent:
    """
    <module_purpose>
    DocLib Swarm Supervisor Agent for orchestrating execution via specialized sub-agents.
    </module_purpose>
    <contract>
    - Precondition: Receives a valid task and current swarm state.
    - Postcondition: Determines the optimal next routing hop based on strictly evaluated state.
    - Error Handling: Relies on structured output constraints to prevent hallucinatory routes.
    </contract>
    """
    def __init__(self, llm):
        self.llm = llm

    @staticmethod
    def _fallback_route(state: SwarmState) -> str:
        if not state.artifacts.get("code"):
            return "coder"
        if state.artifacts.get("review_approved") is not True:
            return "coder" if "review_approved" in state.artifacts else "reviewer"
        if state.artifacts.get("security_approved") is not True:
            return "coder" if "security_approved" in state.artifacts else "secops"
        return "finish"

    async def route(self, state: SwarmState) -> SwarmState:
        logger.info("Supervisor evaluating task routing via LLM")
        
        system_prompt = registry.get(PromptType.SWARM_SUPERVISOR)
        human_msg_content = json.dumps(
            {
                "task": state.task,
                "current_agent": state.current_agent,
                "artifacts": state.artifacts,
                "message_count": len(state.messages),
            },
            ensure_ascii=False,
            default=str,
        )

        try:
            structured_llm = self.llm.with_structured_output(SwarmRouteDecision)
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_msg_content),
            ]
            decision = await structured_llm.ainvoke(messages)
            
            logger.info(f"Supervisor routed to: {decision.next_agent}. Reason: {decision.reasoning}")
            
            if decision.next_agent == "finish":
                state.is_complete = True
            else:
                state.current_agent = decision.next_agent
        except Exception:
            logger.exception("Supervisor LLM routing failed")
            fallback = self._fallback_route(state)
            if fallback == "finish":
                state.is_complete = True
            else:
                state.current_agent = fallback
            
        return state

def create_swarm_workflow(supervisor_llm, specialized_agents: Dict[str, Any]) -> StateGraph:
    workflow = StateGraph(SwarmState)
    
    supervisor = SupervisorAgent(supervisor_llm)
    workflow.add_node("supervisor", supervisor.route)
    
    for name, agent in specialized_agents.items():
        workflow.add_node(name, agent.execute)
        
    workflow.set_entry_point("supervisor")
    
    def router(state: SwarmState):
        if state.is_complete:
            return END
        return state.current_agent

    def agent_router(state: SwarmState):
        if state.is_complete:
            return END
        if state.current_agent in specialized_agents:
            return state.current_agent
        return "supervisor"

    workflow.add_conditional_edges(
        "supervisor",
        router,
        {name: name for name in specialized_agents.keys()} | {END: END}
    )
    
    for name in specialized_agents.keys():
        workflow.add_conditional_edges(
            name,
            agent_router,
            {k: k for k in specialized_agents.keys()} | {"supervisor": "supervisor", END: END}
        )
        
    return workflow.compile()
