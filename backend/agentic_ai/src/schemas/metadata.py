from pydantic import BaseModel, Field

class CreateDocument(BaseModel):
    title: str = Field(description="<constraints>The formal title of the document. MUST be a concise string (max 100 characters) that accurately reflects the topic.</constraints>")
    description: str = Field(description="<input_context>A brief, engaging 1-2 sentence summary of the document's core content, intended for display in document cards or search results.</input_context>")
    format: str = Field(description="<critical_instructions>MUST be exactly 'json' (for standard interactive UI block editing) or 'latex' (for mathematics/scientific typesetting).</critical_instructions>")
    content: str = Field(
        description=(
            "<output_format>\n"
            "The main body of the document. \n"
            "<critical_instructions>For JSON format: MUST be a valid JSON STRING representing an ARRAY of Editor blocks.</critical_instructions>\n"
            "<critical_instructions>For LaTeX format: MUST be raw LaTeX body content ONLY (no documentclass or begin document).</critical_instructions>\n"
            "Calling the `inspect_ui_components` tool is a required first step before generating advanced UI blocks. \n"
            "This is mandatory because the workspace has over 200 custom blocks with specific JSON schemas that must be followed exactly. \n"
            "For LaTeX, the workspace supports over 1000 macros via Tectonic compilation.\n"
            "</output_format>"
        )
    )

class UpdateDocument(BaseModel):
    document_id: str = Field(description="<constraints>The exact, valid unique identifier of the document to be updated. Ensure this matches the ID obtained from search or list endpoints.</constraints>")
    new_content: str = Field(
        description=(
            "<output_format>\n"
            "The new content for the document. \n"
            "<critical_instructions>For JSON format: MUST be a valid JSON string of an array containing FULL Editor block objects.</critical_instructions>\n"
            "<critical_instructions>For LaTeX format: MUST be valid raw LaTeX code.</critical_instructions>\n"
            "Calling the `inspect_ui_components` tool is a required first step before generating advanced UI blocks. \n"
            "This is mandatory to read the frontend source code and ensure you use the exact formats supported by this workspace.\n"
            "</output_format>"
        )
    )
