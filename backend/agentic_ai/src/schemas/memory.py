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

class EntityRelation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source: str = Field(min_length=1, max_length=200, description="<critical_instructions>Source entity name or concept extracted from text.</critical_instructions>")
    relation: str = Field(min_length=1, max_length=100, description="<critical_instructions>Action predicate or relationship verb connecting the source and target entities.</critical_instructions>")
    target: str = Field(min_length=1, max_length=200, description="<critical_instructions>Target entity name or concept related to the source entity.</critical_instructions>")

class ExtractedGraph(BaseModel):
    model_config = ConfigDict(extra="ignore")

    relations: List[EntityRelation] = Field(default_factory=list, description="<critical_instructions>List of entity relationship triplets extracted for knowledge graph construction.</critical_instructions>")
