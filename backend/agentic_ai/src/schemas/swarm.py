from typing import Dict, Any, List, Literal
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field

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

class SwarmRouteDecision(BaseModel):
    next_agent: Literal["coder", "secops", "reviewer", "finish"] = Field(
        ..., description="<critical_instructions>The next agent to route the task to, or 'finish' if complete.</critical_instructions>"
    )
    reasoning: str = Field(..., description="<critical_instructions>Why this route was chosen.</critical_instructions>")
