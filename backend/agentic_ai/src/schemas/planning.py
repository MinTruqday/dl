from typing import List
from pydantic import BaseModel, Field

class PlanStep(BaseModel):
    agent: str = Field(
        description="The precise name of the execution agent assigned to this step. CRITICAL: MUST be a valid registered agent (e.g., 'Action', 'Knowledge', 'GenerationAgent', 'InterpreterAgent', 'EngineAgent', 'Reasoning')."
    )
    task: str = Field(
        description="Detailed, actionable task description. CRITICAL: MUST clearly state what needs to be done, the expected inputs, and the required format of the output."
    )

class PlanStepGroup(BaseModel):
    parallel_steps: List[PlanStep] = Field(
        description="CRITICAL: A list of tasks that have NO inter-dependencies and MUST be executed in parallel to save time. MUST contain at least 1 step. If steps depend on each other, they belong in separate PlanStepGroups."
    )

class ExecutionPlan(BaseModel):
    reasoning: str = Field(
        description="A step-by-step logical chain explaining why the task was broken down this way, how inter-dependencies were identified, and why the parallel/sequential structure was chosen."
    )
    steps: List[PlanStepGroup] = Field(
        description="CRITICAL: An ordered list of PlanStepGroups. Groups MUST run strictly sequentially (group 2 only starts after group 1 is complete). Steps within a single group run concurrently. Design to maximize parallel execution."
    )

