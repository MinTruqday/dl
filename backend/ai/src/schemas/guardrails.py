from pydantic import BaseModel, ConfigDict, Field


class SecurityAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_safe: bool = Field(
        description="True when the input contains no prompt injection or unauthorized override"
    )
    risk_score: float = Field(
        ge=0,
        le=1,
        description="Risk score from zero to one",
    )
    threat_category: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9_:-]+$",
        description="Normalized threat category or none",
    )
    reason: str = Field(
        min_length=1,
        max_length=2000,
        description="Objective reason for the safety classification",
    )
