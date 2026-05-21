from pydantic import BaseModel
from typing import Optional

class CompileRequest(BaseModel):
    content: str
    job_id: str
    callback_url: Optional[str] = None
