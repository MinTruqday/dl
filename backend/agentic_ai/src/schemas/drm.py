from pydantic import BaseModel, Field
from typing import Optional

class DRMPolicyOutput(BaseModel):
    decision: str = Field(
        description="<critical_instructions>MUST be exactly one of: LEVEL_0 (No DRM), LEVEL_1 (Basic tracking), LEVEL_2 (Watermarking & tracking), LEVEL_3 (Encryption & strict tracking), or BLOCKED (Access denied). Determine this based on the trust profile and document risk.</critical_instructions>"
    )
    reasoning: str = Field(
        description="<internal_thought>A short, one-sentence technical justification for this decision. (e.g., 'User has high trust score and IP is stable, granting LEVEL_0').</internal_thought>"
    )
    enable_visual_watermark: bool = Field(
        description="<metis_constraint>Set to true if visual deterrence (e.g., an overlay across the document) is required due to elevated risk.</metis_constraint>"
    )
    enable_micro_dots: bool = Field(
        description="<metis_constraint>Set to true if steganography forensic tracking is needed to trace leaks back to the specific user session.</metis_constraint>"
    )
    enable_aes_encryption: bool = Field(
        description="<metis_constraint>Set to true to wrap the document in a secure .doclib AES-GCM container to prevent offline extraction.</metis_constraint>"
    )
    hardware_binding_strict: bool = Field(
        description="<critical_instructions>Set to true to lock the decryption key strictly to the client's hardware signature (MAC address, CPU ID). Use ONLY for LEVEL_3.</critical_instructions>"
    )

class DRMContextRequest(BaseModel):
    user_id: str
    document_id: str
    client_ip: str
    user_tier: Optional[str] = "BASIC"
    document_type: Optional[str] = "standard"
