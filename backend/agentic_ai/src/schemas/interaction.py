from typing import Annotated, Optional

from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """
    Defines the payload for incoming chat requests to Metis.
    Constraint: Ensure `thread_id` is supplied to maintain context window continuity.
    """
    query: str = Field(min_length=1, max_length=100000, description="<critical_instructions>The main user query to respond to.</critical_instructions>")
    user_id: str = Field(default="", max_length=128, description="<input_context>The ID of the requesting user.</input_context>")
    document_ids: list[Annotated[str, Field(min_length=1, max_length=128)]] = Field(default_factory=list, max_length=100, description="<input_context>List of relevant document IDs.</input_context>")
    useWeb: bool = Field(default=False, description="<conditional_output>Whether to use web search.</conditional_output>")
    thinking: bool = Field(default=False, description="<conditional_output>Whether to enable deeper orchestration with public progress status.</conditional_output>")
    approve_tools: bool = Field(default=False, description="<conditional_output>Whether the user explicitly approved sensitive tool execution for this request.</conditional_output>")
    image_data: Optional[str] = Field(default=None, max_length=28000000, description="<input_context>Base64 encoded image data if attached.</input_context>")
    file_data: Optional[str] = Field(default=None, max_length=28000000, description="<input_context>Base64 encoded file data if attached.</input_context>")
    folder_data: Optional[str] = Field(default=None, max_length=28000000, description="<input_context>Base64 encoded folder context.</input_context>")
    session_id: Optional[str] = Field(default=None, max_length=128, description="<input_context>Session identifier for context retrieval.</input_context>")
    conversation_history: list[dict] = Field(default_factory=list, max_length=100, description="<input_context>Previous messages in the thread.</input_context>")
    token: Optional[str] = Field(default=None, max_length=8192, description="<critical_instructions>Authentication token of the user.</critical_instructions>")
    attachments: list[dict] = Field(default_factory=list, max_length=100, description="<input_context>List of attached files.</input_context>")
