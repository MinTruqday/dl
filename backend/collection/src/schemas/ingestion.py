from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

class Collection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["NXBGD"] = "NXBGD"
    pages: int = 12
    max_documents: int = Field(default=1, ge=1, le=10)
    force_recrawl: bool = False

    @field_validator("pages")
    @classmethod
    def validate_pages(cls, value, info):
        try:
            pages = int(value)
        except (TypeError, ValueError):
            raise ValueError("Số trang phải là số nguyên")
        if pages < 1 or pages > 12:
            raise ValueError("Khối mục tiêu phải nằm trong khoảng từ 1 đến 12")
        return pages
