from pydantic import BaseModel, Field
from typing import Optional
from src.schemas.auth import Tier

class WatermarkConfig(BaseModel):
    enabled: bool = Field(default=False, description="<critical_instructions>Whether visual watermark is enabled.</critical_instructions>")
    text: str = Field(default="", description="<input_context>Contextual text for watermark (User Email, IP, Session ID, Timestamp).</input_context>")
    opacity: float = Field(default=0.15, description="<constraints>Opacity float between 0.05 and 0.5.</constraints>")
    font_size: int = Field(default=16, description="<constraints>Font size in pixels.</constraints>")
    color: str = Field(default="#888888", description="<constraints>Color hex code.</constraints>")

class AntiExfiltrationFlags(BaseModel):
    block_print: bool = Field(default=False, description="<critical_instructions>Block printing and Ctrl+P.</critical_instructions>")
    block_copy: bool = Field(default=False, description="<critical_instructions>Block text copying and selection.</critical_instructions>")
    block_screenshot: bool = Field(default=False, description="<critical_instructions>Trigger screen blur on focus loss.</critical_instructions>")

class AESKeySession(BaseModel):
    key_id: str = Field(description="<critical_instructions>Unique key identifier stored in Redis.</critical_instructions>")
    key_hex: str = Field(description="<critical_instructions>AES-256-GCM hex key string.</critical_instructions>")
    ttl_seconds: int = Field(default=300, description="<constraints>Time-To-Live in seconds for temporary key.</constraints>")

class DRMPolicyOutput(BaseModel):
    decision: str = Field(description="<critical_instructions>MUST be one of: LEVEL_0, LEVEL_1, LEVEL_2, LEVEL_3, BLOCKED.</critical_instructions>")
    reasoning: str = Field(description="<decision_context>Concise technical justification for the policy decision.</decision_context>")
    watermark: WatermarkConfig = Field(default_factory=WatermarkConfig, description="<critical_instructions>Watermark configuration.</critical_instructions>")
    anti_exfiltration: AntiExfiltrationFlags = Field(default_factory=AntiExfiltrationFlags, description="<critical_instructions>Anti-exfiltration flags.</critical_instructions>")
    enable_aes_encryption: bool = Field(default=False, description="<metis_constraint>Enable AES-256-GCM container.</metis_constraint>")
    hardware_binding_strict: bool = Field(default=False, description="<critical_instructions>Lock decryption key to device fingerprint.</critical_instructions>")

class DRMContextRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128, description="<input_context>User identifier used for policy and license lookup.</input_context>")
    document_id: str = Field(min_length=1, max_length=128, description="<input_context>Document identifier whose access policy is evaluated.</input_context>")
    client_ip: str = Field(min_length=1, max_length=64, description="<security_context>Client network address included in risk evaluation.</security_context>")
    user_tier: Optional[Tier] = Field(default=Tier.BASIC, description="<decision_context>Subscription tier used by the rights policy.</decision_context>")
    document_type: Optional[str] = Field(default="standard", min_length=1, max_length=64, description="<decision_context>Document protection category used by the rights policy.</decision_context>")
    device_fingerprint: Optional[str] = Field(default=None, max_length=512, description="<security_context>Optional device binding fingerprint for strict access decisions.</security_context>")
