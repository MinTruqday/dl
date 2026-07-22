from typing import Optional

from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """
    Defines the payload for incoming chat requests to Metis.
    Constraint: Ensure `thread_id` is supplied to maintain context window continuity.
    """
    query: str = Field(description="<critical_instructions>The main user query to respond to.</critical_instructions>")
    user_id: str = Field(default="", description="<input_context>The ID of the requesting user.</input_context>")
    document_ids: Optional[list] = Field(default_factory=list, description="<input_context>List of relevant document IDs.</input_context>")
    useWeb: bool = Field(default=False, description="<conditional_output>Whether to use web search.</conditional_output>")
    thinking: bool = Field(default=False, description="<conditional_output>Whether to stream internal thinking.</conditional_output>")
    image_data: Optional[str] = Field(default=None, description="<input_context>Base64 encoded image data if attached.</input_context>")
    file_data: Optional[str] = Field(default=None, description="<input_context>Base64 encoded file data if attached.</input_context>")
    folder_data: Optional[str] = Field(default=None, description="<input_context>Base64 encoded folder context.</input_context>")
    session_id: Optional[str] = Field(default=None, description="<input_context>Session identifier for context retrieval.</input_context>")
    conversation_history: Optional[list] = Field(default_factory=list, description="<input_context>Previous messages in the thread.</input_context>")
    token: Optional[str] = Field(default=None, description="<critical_instructions>Authentication token of the user.</critical_instructions>")
    attachments: Optional[list] = Field(default_factory=list, description="<input_context>List of attached files.</input_context>")
