from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class HighlightCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    text: str = Field(description="<critical_instructions>Highlighted text snippet content</critical_instructions>")
    color: str = Field(default="#e4e4e7", description="<critical_instructions>Highlight background hex color code</critical_instructions>")
    start_offset: int = Field(default=0, description="<critical_instructions>Starting character position offset</critical_instructions>")
    end_offset: int = Field(default=0, description="<critical_instructions>Ending character position offset</critical_instructions>")
    note: str = Field(default="", description="<critical_instructions>Optional user annotation note on the highlight</critical_instructions>")

class HighlightNoteUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    note: str = Field(description="<critical_instructions>Updated user annotation note</critical_instructions>")
