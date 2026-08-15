from typing import List, Literal
from pydantic import BaseModel, ConfigDict, Field

class MemoryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    content: str = Field(description="<critical_instructions>The content of the memory to save.</critical_instructions>")
    category: Literal["fact", "preference"] = Field(
        "fact",
        description="<critical_instructions>Durable user fact or preference.</critical_instructions>",
    )

class MemoryOperation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    add: List[MemoryItem] = Field(default_factory=list, description="<critical_instructions>List of new memories to add based on the conversation.</critical_instructions>")
