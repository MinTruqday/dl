from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

class HistoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

class SessionCreate(HistoryRequest):
    document_id: Optional[str] = Field(default=None, min_length=1, max_length=128, description="<input_context>Optional document associated with the conversation.</input_context>")
    first_query: str = Field(default="", max_length=100000, description="<input_context>Initial user request used to derive the session title.</input_context>")
    mode: Literal["chat", "work", "goal", "learn", "plan"] = Field(
        default="chat",
        description="<conditional_output>Conversation execution mode selected for the new session.</conditional_output>",
    )

class SessionTitleUpdate(HistoryRequest):
    title: str = Field(min_length=1, max_length=200, description="<input_context>New conversation title.</input_context>")


class SessionStateUpdate(HistoryRequest):
    is_pinned: Optional[bool] = Field(
        default=None,
        description="<input_context>Optional pinned state to apply to the conversation.</input_context>",
    )
    is_archived: Optional[bool] = Field(
        default=None,
        description="<input_context>Optional archived state to apply to the conversation.</input_context>",
    )

class MessageCreate(HistoryRequest):
    role: Literal["user"] = Field(default="user", description="<critical_instructions>Public history writes may append only authenticated user messages.</critical_instructions>")
    content: str = Field(min_length=1, max_length=100000, description="<input_context>Message content to append.</input_context>")
    attachments: list[dict] = Field(default_factory=list, max_length=100, description="<input_context>Bounded attachment metadata associated with the message.</input_context>")
