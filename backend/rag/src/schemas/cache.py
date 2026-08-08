from typing import List, Optional
from pydantic import BaseModel, Field

class CacheGetRequest(BaseModel):
    query_text: str = Field(description="Nội dung câu hỏi")
    query_vector: Optional[List[float]] = Field(default=None, description="Vector truy vấn tương ứng nếu có")

class CacheSetRequest(BaseModel):
    query_text: str = Field(description="Nội dung câu hỏi")
    response_text: str = Field(description="Nội dung câu trả lời")
    query_vector: Optional[List[float]] = Field(default=None, description="Vector biểu diễn ngữ nghĩa câu hỏi")

class CacheGetResponse(BaseModel):
    hit: bool
    response: Optional[str] = None
