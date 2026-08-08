from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class BookmarkFolderBase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = Field(description="<critical_instructions>Name of the bookmark folder collection</critical_instructions>")
    color: Optional[str] = Field(default="#3b82f6", description="<critical_instructions>Folder indicator color</critical_instructions>")

class BookmarkFolderCreate(BookmarkFolderBase):
    pass

class BookmarkFolderAssign(BaseModel):
    model_config = ConfigDict(extra="ignore")
    folder_id: str = Field(description="<critical_instructions>Target bookmark folder identifier</critical_instructions>")
    document_ids: List[str] = Field(description="<critical_instructions>List of document identifiers to assign</critical_instructions>")
