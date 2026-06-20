from pydantic import BaseModel, Field


class CreateDocument(BaseModel):
    title: str = Field(description="Tiêu đề tài liệu")
    description: str = Field(description="Bản tóm tắt ngắn của tài liệu")
    format: str = Field(
        description="Phải là định dạng JSON hoặc LaTeX"
    )
    content: str = Field(
        description=(
            "The main body of the document "
            "For json format MUST be a valid JSON STRING representing an ARRAY of Editor blocks "
            "For latex format MUST be raw LaTeX body content ONLY no documentclass or begin document "
            "Use advanced blocks and tags appropriate for the requested format"
        )
    )


class UpdateDocument(BaseModel):
    document_id: str = Field(description="Định danh tài liệu cần cập nhật")
    new_content: str = Field(
        description=(
            "The new content for the document "
            "For json format new_content MUST be a valid JSON string of an array containing FULL Editor block objects "
            "For latex format new_content MUST be valid raw LaTeX code"
        )
    )