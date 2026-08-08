from typing import List
from pydantic import BaseModel, Field

class EmbedQueryRequest(BaseModel):
    text: str = Field(description="Văn bản cần tạo vector embedding")

class EmbedBatchRequest(BaseModel):
    texts: List[str] = Field(description="Danh sách các văn bản cần tạo vector embedding")

class EmbeddingResponse(BaseModel):
    embedding: List[float] = Field(description="Vector biểu diễn ngữ nghĩa")

class BatchEmbeddingResponse(BaseModel):
    embeddings: List[List[float]] = Field(description="Danh sách vector biểu diễn ngữ nghĩa")
    count: int = Field(description="Số lượng vector đã trích xuất")
