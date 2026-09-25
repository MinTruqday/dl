from typing import List, Optional

from pydantic import BaseModel, Field


class CacheGetRequest(BaseModel):
    query_text: str = Field(description="Question text")
    query_vector: Optional[List[float]] = Field(
        default=None, description="Corresponding query vector when available"
    )


class CacheSetRequest(BaseModel):
    query_text: str = Field(description="Question text")
    response_text: str = Field(description="Answer text")
    query_vector: Optional[List[float]] = Field(
        default=None, description="Semantic vector for the question"
    )


class CacheGetResponse(BaseModel):
    hit: bool
    response: Optional[str] = None
