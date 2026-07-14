from typing import List
from pydantic import BaseModel, Field

class ThoughtBranch(BaseModel):
    approach_name: str = Field(..., description="<critical_instructions>Name of the approach.</critical_instructions>")
    implementation: str = Field(..., description="<critical_instructions>The code implementation for this approach.</critical_instructions>")

class MCTSThoughts(BaseModel):
    branches: List[ThoughtBranch] = Field(..., description="<critical_instructions>Exactly 3 different approaches.</critical_instructions>")

class MCTSEvaluation(BaseModel):
    score: float = Field(..., description="<critical_instructions>Score from 0.0 to 1.0 evaluating the implementation quality.</critical_instructions>")
