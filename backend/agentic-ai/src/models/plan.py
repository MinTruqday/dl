from pydantic import BaseModel, Field
from typing import List

class PlanStep(BaseModel):
    agent: str = Field(description="Tên của Agent thực thi (VD: CodeInterpreter, SearchEngine, ActionAgent, DraftGenerator, KnowledgeAgent)")
    task: str = Field(description="Nhiệm vụ cụ thể mà Agent này cần thực thi, mô tả chi tiết bằng tiếng Việt")

class ExecutionPlan(BaseModel):
    steps: List[PlanStep] = Field(description="Danh sách thứ tự các bước để hoàn thành yêu cầu của người dùng")
