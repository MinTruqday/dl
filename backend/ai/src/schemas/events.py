import json
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("payload", "payload_template", check_fields=False)
    @classmethod
    def validate_payload_size(cls, value):
        if len(json.dumps(value, ensure_ascii=False, default=str).encode()) > 65536:
            raise ValueError("Event payload exceeds 64 KiB")
        return value


class WebhookPayload(EventRequest):
    event_type: Literal[
        "webhook",
        "document_uploaded",
        "user_query",
        "system_heartbeat",
        "document_deleted",
        "user_registered",
    ] = Field(
        default="webhook",
        description="Loại sự kiện nhận vào",
    )
    source: str = Field(
        default="external",
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_.:-]+$",
        description="Nguồn phát sự kiện",
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dữ liệu của sự kiện",
    )


class CreateScheduleRequest(EventRequest):
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Tên lịch chạy",
    )
    interval_seconds: int = Field(
        ge=60,
        le=2592000,
        description="Khoảng cách giữa các lần chạy theo giây",
    )
    event_type: Literal["system_heartbeat", "document_uploaded", "user_query", "webhook"] = Field(
        default="system_heartbeat",
        description="Loại sự kiện định kỳ",
    )
    payload_template: Dict[str, Any] = Field(
        default_factory=dict, description="Mẫu dữ liệu sự kiện"
    )
    enabled: bool = Field(
        default=True,
        description="Trạng thái hoạt động của lịch",
    )


class ManualTriggerRequest(EventRequest):
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dữ liệu giới hạn chuyển cho bộ xử lý sự kiện",
    )


class ScheduleResponse(EventRequest):
    schedule_id: str = Field(
        description="Mã lịch chạy"
    )
    name: str = Field(description="Tên lịch chạy")
    interval_seconds: int = Field(
        description="Khoảng cách giữa các lần chạy theo giây"
    )
    event_type: str = Field(
        description="Loại sự kiện định kỳ"
    )
    enabled: bool = Field(
        description="Trạng thái hoạt động của lịch"
    )
    run_count: int = Field(
        description="Tổng số lần lịch đã chạy"
    )
    last_run_at: Optional[str] = Field(
        default=None, description="Thời điểm chạy gần nhất"
    )
