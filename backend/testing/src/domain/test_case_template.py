from typing import Any, Literal

from pydantic import BaseModel, Field


TemplateType = Literal["functional", "api", "rbac", "state", "bva"]


class TestCaseTemplateCreate(BaseModel):
    name: str = Field(min_length=2, max_length=300)
    template_type: TemplateType
    description: str = Field(default="", max_length=5000)
    definition: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list, max_length=100)


class TestCaseTemplatePatch(BaseModel):
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=2, max_length=300)
    template_type: TemplateType | None = None
    description: str | None = Field(default=None, max_length=5000)
    definition: dict[str, Any] | None = None
    tags: list[str] | None = Field(default=None, max_length=100)


class TestCaseTemplateArchive(BaseModel):
    expected_revision: int = Field(ge=1)
    reason: str = Field(min_length=2, max_length=2000)
