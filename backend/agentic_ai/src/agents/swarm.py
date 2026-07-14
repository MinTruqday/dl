from typing import Dict, Any, List, Literal
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from loguru import logger
from src.core.registry import PromptType, registry

class SwarmState(BaseModel):
    """
    <schema_definition>
    <purpose>Maintains the global state of the Multi-Agent Swarm execution.</purpose>
    <metis_constraint>Must be strictly typed and validated at every state transition.</metis_constraint>
    </schema_definition>
    """
    task: str
    context: Dict[str, Any] = Field(default_factory=dict)
    messages: List[BaseMessage] = Field(default_factory=list)
    current_agent: str = "supervisor"
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    is_complete: bool = False

class RouteDecision(BaseModel):
    next_agent: Literal["coder", "secops", "reviewer", "finish"] = Field(
        ..., description="The next agent to route the task to, or 'finish' if complete."
    )
    reasoning: str = Field(..., description="Why this route was chosen.")

class SupervisorAgent:
    """
    <agent_role>
    <identity>Swarm Supervisor</identity>
    <responsibility>Analyzes the task state and orchestrates execution by delegating to specialized agents.</responsibility>
    <metis_behavior>Acts as the master router, relying on strict logic and zero hallucination.</metis_behavior>
    </agent_role>
    """
    def __init__(self, llm):
        self.llm = llm

    async def route(self, state: SwarmState) -> SwarmState:
        logger.info("Supervisor evaluating task routing via LLM")
        
        system_prompt = registry.get(PromptType.SWARM_SUPERVISOR)
        human_msg_content = (
            f"Current Task: {state.task}\n"
            f"Artifacts gathered: {list(state.artifacts.keys())}\n"
            f"Message history length: {len(state.messages)}\n"
            "Determine the next route."
        )

        
        try:
            structured_llm = self.llm.with_structured_output(RouteDecision)
            messages = [SystemMessage(content=system_prompt), HumanMessage(content="Determine the next route.")]
            decision = await structured_llm.ainvoke(messages)
            
            logger.info(f"Supervisor routed to: {decision.next_agent}. Reason: {decision.reasoning}")
            
            if decision.next_agent == "finish":
                state.is_complete = True
            else:
                state.current_agent = decision.next_agent
        except Exception as e:
            logger.exception("Supervisor LLM routing failed")
            state.is_complete = True
            
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

    workflow.add_conditional_edges(
        "supervisor",
        router,
        {name: name for name in specialized_agents.keys()} | {END: END}
    )
    
    for name in specialized_agents.keys():
        workflow.add_edge(name, "supervisor")
        
    return workflow.compile()
