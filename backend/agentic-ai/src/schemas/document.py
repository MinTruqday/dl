from pydantic import BaseModel, Field

class CreateDocument(BaseModel):
    title: str = Field(description="The title of the document.")
    description: str = Field(description="A short summary of the document.")
    format: str = Field(description="Must be 'json' (for Editor.js) or 'latex' (for LaTeX).")
    content: str = Field(
        description=(
            "The main body of the document. "
            "For 'json' format: MUST be a valid JSON STRING representing an ARRAY of Editor.js blocks "
            "(e.g., [{'type': 'paragraph', 'data': {'text': '...'}}, {'type': 'header', 'data': {'text': '...', 'level': 2}}, {'type': 'list', 'data': {'style': 'unordered', 'items': [...]}}, {'type': 'table', 'data': {'withHeadings': true, 'content': [...]}}]). "
            "For 'latex' format: MUST be raw LaTeX body content ONLY (no \\documentclass or \\begin{document}). "
            "Use advanced blocks/tags appropriate for the requested format."
        )
    )

class UpdateDocument(BaseModel):
    document_id: str = Field(description="The ID of the document to update.")
    new_content: str = Field(
        description=(
            "The new content for the document. "
            "For json format, new_content MUST be a valid JSON string of an array containing FULL Editor.js block objects (paragraph, header, list, table, etc.). "
            "For latex format, new_content MUST be valid raw LaTeX code."
        )
    )
