from pydantic import BaseModel, Field

class CoderOutput(BaseModel):
    code: str = Field(..., description="<critical_instructions>The generated Python code.</critical_instructions>")
    logic_explanation: str = Field(..., description="<critical_instructions>Brief explanation of the logic.</critical_instructions>")
