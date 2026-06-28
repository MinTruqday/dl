from pydantic import BaseModel, Field

class CreateDocument(BaseModel):
    title: str = Field(description="The title of the document")
    description: str = Field(description="A brief summary of the document")
    format: str = Field(description="Must be JSON or LaTeX format")
    content: str = Field(
        description=(
            "The main body of the document. "
            "For JSON format: MUST be a valid JSON STRING representing an ARRAY of Editor blocks. "
            "For LaTeX format: MUST be raw LaTeX body content ONLY (no documentclass or begin document). "
            "CRITICAL: The workspace has over 200 custom EditorJS blocks (e.g. DocLibChart, DocLibKanban). If you need to generate advanced UI blocks, "
            "YOU MUST CALL the `inspect_ui_components` tool (e.g., query='Chart') BEFOREHAND to read its TypeScript source code and infer the exact JSON schema. Do not guess. "
            "For LaTeX, the workspace supports over 1000 macros via Tectonic compilation."
        )
    )

class UpdateDocument(BaseModel):
    document_id: str = Field(description="The unique identifier of the document to update")
    new_content: str = Field(
        description=(
            "The new content for the document. "
            "For JSON format: MUST be a valid JSON string of an array containing FULL Editor block objects. "
            "For LaTeX format: MUST be valid raw LaTeX code. "
            "CRITICAL: If generating advanced UI blocks, YOU MUST CALL the `inspect_ui_components` tool first "
            "to read the frontend source code and ensure you use the exact formats supported by this workspace. Do not guess."
        )
    )
