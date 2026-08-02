from datetime import datetime

from pydantic import BaseModel, Field

class Registration(BaseModel):
    document_id: str
    user_id: str

class Confirmation(BaseModel):
    file_id: str
    aes_key: str

class Acquisition(BaseModel):
    file_id: str
    client_public_key: str
    hardware_signature: str

class Token(BaseModel):
    encrypted_aes_key: str
    expires_at: datetime | None = None
    rights: dict[str, bool] = Field(default_factory=dict)
    profile: str = "doclib-drm-2026"
