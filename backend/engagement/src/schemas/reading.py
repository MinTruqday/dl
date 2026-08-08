from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class ProgressUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    document_id: str = Field(description="<critical_instructions>Identifier of the document being read</critical_instructions>")
    progress_percentage: float = Field(description="<critical_instructions>Reading progress percentage between 0 and 100</critical_instructions>")

class ReadingPreferenceUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    theme: Optional[str] = Field(default=None, description="<critical_instructions>Reader UI theme mode</critical_instructions>")
    font_size: Optional[int] = Field(default=None, description="<critical_instructions>Reader font size in pixels</critical_instructions>")
    line_height: Optional[float] = Field(default=None, description="<critical_instructions>Reader text line height</critical_instructions>")
    font_family: Optional[str] = Field(default=None, description="<critical_instructions>Reader typography font family</critical_instructions>")
    letter_spacing: Optional[float] = Field(default=None, description="<critical_instructions>Letter spacing adjustment</critical_instructions>")
    is_dyslexic_mode: Optional[bool] = Field(default=None, description="<critical_instructions>Dyslexic friendly font toggling</critical_instructions>")
