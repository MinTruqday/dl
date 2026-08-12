from typing import Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

class Collection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["AnnaArchive", "NXBST", "NXBGD", "CTAN"]
    pages: Union[int, str] = 1
    max_documents: int = Field(default=1, ge=1, le=10)

    @field_validator("pages")
    @classmethod
    def validate_pages(cls, value, info):
        source = info.data.get("source")
        if source == "CTAN":
            normalized = str(value).lower()
            if len(normalized) != 1 or not normalized.isalpha():
                raise ValueError("CTAN yêu cầu một chữ cái từ a đến z")
            return normalized
        try:
            pages = int(value)
        except (TypeError, ValueError):
            raise ValueError("Số trang phải là số nguyên")
        if pages < 1 or pages > 100:
            raise ValueError("Số trang phải nằm trong khoảng từ 1 đến 100")
        return pages
