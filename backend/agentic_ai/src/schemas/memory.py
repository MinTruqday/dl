from typing import List, Optional
from pydantic import BaseModel, Field

class MemoryItem(BaseModel):
    id: Optional[str] = Field(None, description="The unique ID of the memory, if updating or deleting an existing memory. Leave empty for new memories.")
    content: str = Field(..., description="The content of the memory to save.")
    category: str = Field("fact", description="The category of the memory. Can be 'fact', 'preference', 'procedure', or 'relationship'.")
    hash: Optional[str] = Field(None, description="MD5 hash of the content to prevent duplication.")
    agent_id: Optional[str] = Field(None, description="ID of the agent that owns or created this memory, for multi-tenant isolation.")
    run_id: Optional[str] = Field(None, description="Execution run ID for contextual grouping.")
    memory_type: str = Field("semantic", description="Type of memory: semantic, episodic, procedural, or entity.")
    expires_at: Optional[str] = Field(None, description="Optional ISO timestamp for when this memory should expire.")
    created_at: Optional[str] = Field(None, description="ISO timestamp of memory creation.")
    updated_at: Optional[str] = Field(None, description="ISO timestamp of last update.")

class MemoryOperation(BaseModel):
    add: List[MemoryItem] = Field(default_factory=list, description="List of new memories to add based on the conversation.")
    update: List[MemoryItem] = Field(default_factory=list, description="List of existing memories to update based on new information in the conversation. Must include the exact existing memory ID.")
    delete: List[str] = Field(default_factory=list, description="List of memory IDs to delete based on the conversation (e.g. user asked to forget something or the information is obsolete).")
