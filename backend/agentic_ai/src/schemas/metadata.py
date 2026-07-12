from pydantic import BaseModel, Field

class CreateDocument(BaseModel):
    title: str = Field(description="The formal title of the document. Must be a concise string (max 100 characters) that accurately reflects the topic.")
    description: str = Field(description="A brief, engaging 1-2 sentence summary of the document's core content, intended for display in document cards or search results.")
    format: str = Field(description="Must be exactly 'json' (for standard interactive UI block editing) or 'latex' (for mathematics/scientific typesetting).")
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
    document_id: str = Field(description="The exact, valid unique identifier of the document to be updated. Ensure this matches the ID obtained from search or list endpoints.")
    new_content: str = Field(
        description=(
            "The new content for the document. "
            "For JSON format: MUST be a valid JSON string of an array containing FULL Editor block objects. "
            "For LaTeX format: MUST be valid raw LaTeX code. "
            "CRITICAL: If generating advanced UI blocks, YOU MUST CALL the `inspect_ui_components` tool first "
            "to read the frontend source code and ensure you use the exact formats supported by this workspace. Do not guess."
        )
    )
