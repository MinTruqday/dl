from typing import List

from pydantic import BaseModel, Field


class EmbedQueryRequest(BaseModel):
    text: str = Field(description="Text to embed")


class EmbedBatchRequest(BaseModel):
    texts: List[str] = Field(description="Texts to embed")


class EmbeddingResponse(BaseModel):
    embedding: List[float] = Field(description="Semantic vector")


class BatchEmbeddingResponse(BaseModel):
    embeddings: List[List[float]] = Field(description="Semantic vectors")
    count: int = Field(description="Number of generated vectors")
