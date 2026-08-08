from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

class MemoryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = Field(None, description="<critical_instructions>The unique ID of the memory, if updating or deleting an existing memory. Leave empty for new memories.</critical_instructions>")
    content: str = Field(description="<critical_instructions>The content of the memory to save.</critical_instructions>")
    category: str = Field("fact", description="<critical_instructions>The category of the memory. Can be 'fact', 'preference', 'procedure', or 'relationship'.</critical_instructions>")
    hash: Optional[str] = Field(None, description="<system_context>SHA-256 hash of the content to prevent duplication.</system_context>")
    agent_id: Optional[str] = Field(None, description="<system_context>ID of the agent that owns or created this memory for multi-tenant isolation.</system_context>")
    run_id: Optional[str] = Field(None, description="<system_context>Execution run ID for contextual grouping.</system_context>")
    memory_type: str = Field("semantic", description="<critical_instructions>Type of memory: semantic, episodic, procedural, or entity.</critical_instructions>")
    expires_at: Optional[str] = Field(None, description="<system_context>Optional ISO timestamp for when this memory should expire.</system_context>")
    created_at: Optional[str] = Field(None, description="<system_context>ISO timestamp of memory creation.</system_context>")
    updated_at: Optional[str] = Field(None, description="<system_context>ISO timestamp of last update.</system_context>")

class MemoryOperation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    add: List[MemoryItem] = Field(default_factory=list, description="<critical_instructions>List of new memories to add based on the conversation.</critical_instructions>")
    update: List[MemoryItem] = Field(default_factory=list, description="<critical_instructions>List of existing memories to update based on new information in the conversation. Must include the exact existing memory ID.</critical_instructions>")
    delete: List[str] = Field(default_factory=list, description="<critical_instructions>List of memory IDs to delete based on the conversation.</critical_instructions>")

class EntityRelation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source: str = Field(min_length=1, max_length=200, description="<critical_instructions>Source entity name or concept extracted from text.</critical_instructions>")
    relation: str = Field(min_length=1, max_length=100, description="<critical_instructions>Action predicate or relationship verb connecting the source and target entities.</critical_instructions>")
    target: str = Field(min_length=1, max_length=200, description="<critical_instructions>Target entity name or concept related to the source entity.</critical_instructions>")

class ExtractedGraph(BaseModel):
    model_config = ConfigDict(extra="ignore")

    relations: List[EntityRelation] = Field(default_factory=list, description="<critical_instructions>List of entity relationship triplets extracted for knowledge graph construction.</critical_instructions>")
