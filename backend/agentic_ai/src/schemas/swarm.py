from typing import Dict, Any, List, Literal
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field

class SwarmState(BaseModel):
    """
    Maintains the global state of the Multi-Agent Swarm execution.
    Constraint: Passed around by LangGraph between specialized agents (coder, reviewer, secops).
    """
    task: str = Field(description="<critical_instructions>The main task assigned to the swarm.</critical_instructions>")
    context: Dict[str, Any] = Field(default_factory=dict, description="<input_context>Shared context dictionary.</input_context>")
    messages: List[BaseMessage] = Field(default_factory=list, description="<input_context>Message history.</input_context>")
    current_agent: str = Field(default="supervisor", description="<conditional_output>The agent currently processing the task.</conditional_output>")
    artifacts: Dict[str, Any] = Field(default_factory=dict, description="<input_context>Generated files and outputs.</input_context>")
    is_complete: bool = Field(default=False, description="<conditional_output>Whether the swarm has completed the task.</conditional_output>")

class SwarmRouteDecision(BaseModel):
    next_agent: Literal["coder", "secops", "reviewer", "finish"] = Field(description="<critical_instructions>The next agent to route the task to, or 'finish' if complete.</critical_instructions>")
    reasoning: str = Field(description="<critical_instructions>Why this route was chosen.</critical_instructions>")
