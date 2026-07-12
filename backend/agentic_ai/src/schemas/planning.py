from typing import List
from pydantic import BaseModel, Field

class PlanStep(BaseModel):
    agent: str = Field(description="The precise name of the execution agent assigned to this step. CRITICAL: MUST be a valid registered agent (e.g., 'planner', 'writer', 'researcher').")
    task: str = Field(description="Detailed, actionable task description. CRITICAL: MUST clearly state what needs to be done, expected inputs, and format of the desired output.")

class PlanStepGroup(BaseModel):
    parallel_steps: List[PlanStep] = Field(description="List of tasks that have no inter-dependencies and must be executed in parallel to save time. Minimum 1 step.")

class ExecutionPlan(BaseModel):
    reasoning: str = Field(description="A step-by-step logical chain explaining why the task was broken down this way and how the dependencies are managed.")
    steps: List[PlanStepGroup] = Field(description="An ordered list of step groups. Groups run strictly sequentially. Steps within a single group run concurrently. Design groups to maximize parallel execution where possible.")
