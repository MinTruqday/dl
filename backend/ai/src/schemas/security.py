from pydantic import BaseModel, ConfigDict, Field


class SecurityOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SecurityEvaluation(SecurityOutput):
    is_malicious: bool = Field(
        description="Đúng khi đầu vào chứa tấn công chèn lệnh vượt rào hoặc yêu cầu độc hại"
    )
    has_pii: bool = Field(
        description="Đúng khi đầu vào lộ dữ liệu định danh cá nhân nhạy cảm"
    )
    has_credentials: bool = Field(
        description="Đúng khi đầu vào chứa thông tin xác thực hoặc bí mật truy cập"
    )
    sanitized_text: str = Field(
        max_length=200000,
        description="Nội dung đầu vào với dữ liệu nhạy cảm được thay bằng REDACTED",
    )
    reason: str = Field(
        max_length=2000,
        description="Lý do ngắn gọn cho phân loại bảo mật",
    )


class JailbreakCheck(SecurityOutput):
    is_jailbreak: bool = Field(
        description="Đúng khi văn bản chứa tấn công chèn lệnh vượt rào hoặc yêu cầu độc hại"
    )
