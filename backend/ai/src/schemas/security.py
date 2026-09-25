from pydantic import BaseModel, ConfigDict, Field


class SecurityOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SecurityEvaluation(SecurityOutput):
    is_malicious: bool = Field(
        description="True when the input contains prompt injection jailbreak or a malicious request"
    )
    has_pii: bool = Field(
        description="True when the input exposes sensitive personally identifiable information"
    )
    has_credentials: bool = Field(
        description="True when the input contains credentials or access secrets"
    )
    sanitized_text: str = Field(
        max_length=200000,
        description="Input with sensitive spans replaced by REDACTED",
    )
    reason: str = Field(
        max_length=2000,
        description="Concise reason for the security classification",
    )


class JailbreakCheck(SecurityOutput):
    is_jailbreak: bool = Field(
        description="True when the text contains prompt injection jailbreak or a malicious request"
    )
