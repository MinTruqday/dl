from typing import List
from pydantic import BaseModel

class RegisterServerRequest(BaseModel):
    name: str
    description: str
    server_type: str
    url: str = None
    command: str = None
    args: List[str] = []
