from pydantic import BaseModel, Field
from typing import Optional

class CompileRequest(BaseModel):
    content: str = Field(..., max_length=100000)
    job_id: str
    callback_url: Optional[str] = None
