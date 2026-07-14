from typing import List
from pydantic import BaseModel, Field

class SubQueries(BaseModel):
    queries: List[str] = Field(description="<critical_instructions>List of up to 3 distinct sub-queries to search. If the original query is simple, return just one query.</critical_instructions>")
