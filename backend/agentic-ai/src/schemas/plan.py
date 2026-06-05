from pydantic import BaseModel, Field
from typing import List

class PlanStep(BaseModel):
    agent: str = Field(description="Name of the execution agent: ToolDispatcher, KnowledgeAgent, CodeInterpreter, SearchEngine, DraftGenerator, ReasoningAgent")
    task: str = Field(description="Specific task description for the agent to execute")

class ExecutionPlan(BaseModel):
    reasoning: str = Field(description="Chain of thought reasoning before decomposing the steps")
    steps: List[PlanStep] = Field(description="Ordered list of execution steps to fulfill the request")
