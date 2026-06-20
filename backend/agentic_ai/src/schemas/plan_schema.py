from typing import List

from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    agent: str = Field(
        description="Tên tác nhân thực thi"
    )
    task: str = Field(description="Mô tả chi tiết tác vụ")


class ExecutionPlan(BaseModel):
    reasoning: str = Field(
        description="Chuỗi suy luận trước khi phân chia các bước"
    )
    steps: List[PlanStep] = Field(
        description="Danh sách các bước thực thi"
    )