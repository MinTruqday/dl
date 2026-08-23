from typing import List, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class PlanNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_-]+$", description="<critical_instructions>Unique stable identifier containing only letters digits underscores or hyphens</critical_instructions>")
    agent: Literal["EngineAgent", "Action", "Knowledge", "Reasoning"] = Field(description="<critical_instructions>Exact registered execution agent name</critical_instructions>")
    task: str = Field(min_length=3, max_length=2000, description="<critical_instructions>Bounded actionable task with a verifiable outcome</critical_instructions>")
    dependencies: List[str] = Field(default_factory=list, max_length=16, description="<critical_instructions>Unique identifiers of earlier nodes that must finish first</critical_instructions>")
    @model_validator(mode="after")
    def validate_dependencies(self):
        if len(self.dependencies) != len(set(self.dependencies)):
            raise ValueError("dependencies must be unique")
        return self

class ExecutionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reasoning: str = Field(min_length=3, max_length=1000, description="<routing_logic>Concise decision summary naming selected agents and dependencies without private reasoning</routing_logic>")
    nodes: List[PlanNode] = Field(min_length=1, max_length=32, description="<critical_instructions>Nonempty topologically ordered DAG executed in parallel where dependencies permit</critical_instructions>")

    @model_validator(mode="after")
    def validate_dag(self):
        seen = set()
        for node in self.nodes:
            if node.id in seen:
                raise ValueError("node identifiers must be unique")
            unknown = [dependency for dependency in node.dependencies if dependency not in seen]
            if unknown:
                raise ValueError("dependencies must reference earlier nodes")
            seen.add(node.id)
        return self
