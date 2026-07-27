from typing import List
from pydantic import BaseModel, Field

class PlanNode(BaseModel):
    id: str = Field(description="<critical_instructions>Unique identifier for this step, e.g., 'step_1', 'step_2'.</critical_instructions>")
    agent: str = Field(description="<critical_instructions>The precise name of the execution agent assigned to this step. MUST be a valid registered agent.</critical_instructions>")
    task: str = Field(description="<critical_instructions>Detailed, actionable task description.</critical_instructions>")
    dependencies: List[str] = Field(default=[], description="<critical_instructions>List of node IDs that must finish before this node can start. Empty list means it can start immediately.</critical_instructions>")

class ExecutionPlan(BaseModel):
    reasoning: str = Field(description="<routing_logic>A concise decision summary naming selected agents and dependencies without private reasoning.</routing_logic>")
    nodes: List[PlanNode] = Field(description="<critical_instructions>A list of PlanNodes forming a DAG. The orchestrator will use topological sorting to execute nodes in parallel where possible.</critical_instructions>")
