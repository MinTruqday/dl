from pydantic import BaseModel, Field

class SecOpsEvaluation(BaseModel):
    is_secure: bool = Field(description="<critical_instructions>True if no critical vulnerabilities found.</critical_instructions>")
    vulnerability_summary: str = Field(description="<critical_instructions>Summary of vulnerabilities.</critical_instructions>")
