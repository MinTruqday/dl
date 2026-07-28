from pydantic import BaseModel, Field

class CoderOutput(BaseModel):
    language: str = Field(default="python", description="<critical_instructions>The implementation language such as python typescript javascript go rust or java.</critical_instructions>")
    code: str = Field(description="<critical_instructions>The complete generated source code without markdown fences.</critical_instructions>")
    logic_explanation: str = Field(description="<critical_instructions>Brief explanation of the logic.</critical_instructions>")
