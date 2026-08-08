from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class RecommendationQuery(BaseModel):
    model_config = ConfigDict(extra="ignore")
    limit: int = Field(default=20, description="<critical_instructions>Maximum number of recommended items</critical_instructions>")
