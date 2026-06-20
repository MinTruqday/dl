import re

with open('backend/core/dependency.py', 'r') as f:
    content = f.read()

# Add CurrentUser and RoleEnum if not there
if "class CurrentUser" not in content:
    schema_code = """
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class RoleEnum(str, Enum):
    GUEST = "guest"
    READER = "reader"
    AUTHOR = "author"
    ADMIN = "admin"

class CurrentUser(BaseModel):
    id: str = Field(alias="_id")
    email: str
    role: RoleEnum = RoleEnum.READER
    permissions: List[str] = []
    is_active: bool = True
    full_name: str = ""
    is_premium: bool = False
    
    class Config:
        populate_by_name = True
        extra = "ignore"
"""
    # Replace the old import from core.schemas.user import RoleEnum, UserInDB
    content = re.sub(r'from core\.schemas\.user import [^\n]+\n', schema_code + '\n', content)
    
    # Replace UserInDB with CurrentUser
    content = content.replace("UserInDB", "CurrentUser")

with open('backend/core/dependency.py', 'w') as f:
    f.write(content)

print("backend/core/dependency.py updated")
