from pydantic import BaseModel, ConfigDict, Field


class PresignedUrlRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filename: str = Field(min_length=1, max_length=255)
    size: int = Field(ge=1, le=100 * 1024 * 1024)
    content_type: str = Field(min_length=1, max_length=150)
    is_system: bool = False
    is_message_attachment: bool = False


class ConfirmUploadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file_path: str = Field(min_length=1, max_length=500)
    filename: str = Field(min_length=1, max_length=255)
    size: int = Field(ge=1, le=100 * 1024 * 1024)
    content_type: str = Field(min_length=1, max_length=150)
    is_system: bool = False
    is_message_attachment: bool = False
