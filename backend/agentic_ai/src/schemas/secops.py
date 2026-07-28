from pydantic import BaseModel, ConfigDict, Field

class SecOpsEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_secure: bool = Field(description="<critical_instructions>True if no critical vulnerabilities found.</critical_instructions>")
    vulnerability_summary: str = Field(min_length=1, max_length=5000, description="<critical_instructions>Evidence based summary of vulnerabilities or a concise clean assessment.</critical_instructions>")
