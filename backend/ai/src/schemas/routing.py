from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field


class StructuredRouting(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ContextQuery(StructuredRouting):
    question: str = Field(
        description="Câu hỏi độc lập đã làm rõ các tham chiếu từ ngữ cảnh"
    )


class GraphRoute(StructuredRouting):
    route: Literal["knowledge", "direct"] = Field(
        description="knowledge khi cần dữ liệu và direct khi không cần truy xuất"
    )


class RetrievalStrategy(StructuredRouting):
    is_simple: bool = Field(
        description="Đúng khi một truy vấn vector đủ để tìm câu trả lời"
    )
    queries: List[str] = Field(
        description="Một đến năm truy vấn ngắn cho tìm kiếm vector"
    )


class QueryOptimization(StructuredRouting):
    question: str = Field(
        description="Truy vấn tìm kiếm ngắn gọn giữ nguyên ý định"
    )


class RouteDecision(StructuredRouting):
    reasoning: str = Field(
        description="Lý do ngắn gọn cho tuyến đã chọn"
    )
    route: Literal["action", "knowledge", "chat"] = Field(
        description="action để dùng công cụ knowledge để truy xuất và chat để trả lời trực tiếp"
    )
    answer: str = Field(
        default="",
        description="Câu trả lời trực tiếp cho tuyến chat và để trống với tuyến khác",
    )


class MultiQueryOutput(StructuredRouting):
    queries: List[str] = Field(
        description="Đúng ba cách diễn đạt khác nhau của truy vấn"
    )


class CrossDocumentQueries(StructuredRouting):
    queries: List[str] = Field(
        min_length=2,
        max_length=100,
        description="Một truy vấn tập trung cho mỗi tài liệu theo đúng thứ tự đầu vào",
    )
