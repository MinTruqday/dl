from typing import List
from pydantic import BaseModel, Field

class PlanStep(BaseModel):
    agent: str = Field(
        description="<critical_instructions>The precise name of the execution agent assigned to this step. MUST be a valid registered agent (e.g., 'Action', 'Knowledge', 'GenerationAgent', 'InterpreterAgent', 'EngineAgent', 'Reasoning').</critical_instructions>"
    )
    task: str = Field(
        description="<critical_instructions>Detailed, actionable task description. MUST clearly state what needs to be done, the expected inputs, and the required format of the output.</critical_instructions>"
    )

class PlanStepGroup(BaseModel):
    parallel_steps: List[PlanStep] = Field(
        description="<critical_instructions>A list of tasks that have NO inter-dependencies and MUST be executed in parallel to save time. MUST contain at least 1 step. If steps depend on each other, they belong in separate PlanStepGroups.</critical_instructions>"
    )

class ExecutionPlan(BaseModel):
    reasoning: str = Field(
        description="<internal_thought>A step-by-step logical chain explaining why the task was broken down this way, how inter-dependencies were identified, and why the parallel/sequential structure was chosen.</internal_thought>"
    )
    steps: List[PlanStepGroup] = Field(
        description="<critical_instructions>An ordered list of PlanStepGroups. Groups MUST run strictly sequentially (group 2 only starts after group 1 is complete). Steps within a single group run concurrently. Design to maximize parallel execution.</critical_instructions>"
    )

