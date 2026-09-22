from pydantic import BaseModel, ConfigDict, Field


class SecurityAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_safe: bool = Field(
        description="Đúng khi đầu vào không chứa tấn công chèn lệnh hoặc ghi đè trái phép"
    )
    risk_score: float = Field(
        ge=0,
        le=1,
        description="Điểm rủi ro từ 0 đến 1",
    )
    threat_category: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9_:-]+$",
        description="Loại mối đe dọa đã chuẩn hóa hoặc none",
    )
    reason: str = Field(
        min_length=1,
        max_length=2000,
        description="Lý do khách quan cho phân loại an toàn",
    )
