from pydantic import BaseModel

class PresignedUrlRequest(BaseModel):
    filename: str
    size: int
    content_type: str
    is_system: bool = False
    is_message_attachment: bool = False

class ConfirmUploadRequest(BaseModel):
    file_path: str
    filename: str
    size: int
    content_type: str
    is_system: bool = False
    is_message_attachment: bool = False
