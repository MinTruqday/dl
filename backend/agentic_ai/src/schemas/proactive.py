from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProactiveOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StatusArgs(ProactiveOutput):
    status: str = Field(min_length=1, max_length=1000, description="<input_context>Concise current task status and material risks.</input_context>")


class SaveKnowledgeArgs(ProactiveOutput):
    id: str = Field(min_length=1, max_length=128, pattern=r"^[a-z0-9_:-]+$", description="<input_context>Stable identifier for the knowledge entry.</input_context>")
    content: str = Field(min_length=1, max_length=2000, description="<input_context>Stable fact that should constrain later decisions.</input_context>")
    category: Literal["task_fact", "env_fact", "path", "bug", "perf"] = Field(description="<input_context>Knowledge classification used for retrieval.</input_context>")


class SaveProceduralArgs(ProactiveOutput):
    id: str = Field(min_length=1, max_length=128, pattern=r"^[a-z0-9_:-]+$", description="<input_context>Stable identifier for the procedural entry.</input_context>")
    content: str = Field(min_length=1, max_length=2000, description="<input_context>Attempt diagnosis failure or verified fix.</input_context>")
    category: Literal["attempt", "bug", "perf"] = Field(description="<input_context>Procedural classification used for retrieval.</input_context>")


class DeleteMemoryArgs(ProactiveOutput):
    id: str = Field(min_length=1, max_length=128, pattern=r"^[a-z0-9_:-]+$", description="<input_context>Identifier of the obsolete memory entry.</input_context>")


class UpdateStatusCall(ProactiveOutput):
    name: Literal["memory_update_status"] = Field(description="<output_format>Memory status operation.</output_format>")
    args: StatusArgs = Field(description="<output_format>Validated status arguments.</output_format>")


class SaveKnowledgeCall(ProactiveOutput):
    name: Literal["memory_save_knowledge"] = Field(description="<output_format>Knowledge persistence operation.</output_format>")
    args: SaveKnowledgeArgs = Field(description="<output_format>Validated knowledge arguments.</output_format>")


class SaveProceduralCall(ProactiveOutput):
    name: Literal["memory_save_procedural"] = Field(description="<output_format>Procedural persistence operation.</output_format>")
    args: SaveProceduralArgs = Field(description="<output_format>Validated procedural arguments.</output_format>")


class DeleteMemoryCall(ProactiveOutput):
    name: Literal["memory_delete"] = Field(description="<output_format>Memory deletion operation.</output_format>")
    args: DeleteMemoryArgs = Field(description="<output_format>Validated deletion arguments.</output_format>")


MemoryToolCall = Annotated[
    Union[
        UpdateStatusCall,
        SaveKnowledgeCall,
        SaveProceduralCall,
        DeleteMemoryCall,
    ],
    Field(discriminator="name"),
]


class MemoryBankActions(ProactiveOutput):
    calls: list[MemoryToolCall] = Field(default_factory=list, max_length=20, description="<output_format>Minimum validated memory operations required by the trajectory.</output_format>")


class MemoryIntervention(ProactiveOutput):
    intervene: bool = Field(description="<output_format>Whether one memory reminder is required for the next action.</output_format>")
    reminder: Optional[str] = Field(default=None, max_length=2000, description="<conditional_output>One concise actionable reminder when intervention is required.</conditional_output>")

    @model_validator(mode="after")
    def validate_intervention(self):
        if self.intervene and not (self.reminder or "").strip():
            raise ValueError("An intervention requires a reminder")
        if not self.intervene and self.reminder is not None:
            raise ValueError("A silent decision cannot include a reminder")
        return self
