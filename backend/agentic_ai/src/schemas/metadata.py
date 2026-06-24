from pydantic import BaseModel, Field

class CreateDocument(BaseModel):
    title: str = Field(description="The title of the document")
    description: str = Field(description="A brief summary of the document")
    format: str = Field(description="Must be JSON or LaTeX format")
    content: str = Field(
        description=(
            "The main body of the document "
            "For json format MUST be a valid JSON STRING representing an ARRAY of Editor blocks "
            "For latex format MUST be raw LaTeX body content ONLY no documentclass or begin document "
            "Use advanced blocks and tags appropriate for the requested format"
        )
    )

class UpdateDocument(BaseModel):
    document_id: str = Field(description="The unique identifier of the document to update")
    new_content: str = Field(
        description=(
            "The new content for the document "
            "For json format new_content MUST be a valid JSON string of an array containing FULL Editor block objects "
            "For latex format new_content MUST be valid raw LaTeX code"
        )
    )
