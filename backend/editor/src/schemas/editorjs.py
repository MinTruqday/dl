from pydantic import BaseModel, Field

class CompileRequest(BaseModel):
    content: str = Field(...)