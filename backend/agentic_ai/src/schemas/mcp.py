from typing import Annotated, List, Literal
from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator

class RegisterServerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=128, description="<input_context>Unique human readable MCP server name.</input_context>")
    description: str = Field(min_length=1, max_length=2000, description="<input_context>Capabilities and intended use of the MCP server.</input_context>")
    server_type: Literal["sse", "streamable_http", "stdio"] = Field(description="<critical_instructions>Supported MCP transport type.</critical_instructions>")
    url: str | None = Field(default=None, max_length=2048, description="<input_context>Remote MCP endpoint for network transports.</input_context>")
    command: str | None = Field(default=None, max_length=1024, description="<security_context>Executable command for approved local transports.</security_context>")
    args: List[Annotated[str, Field(min_length=1, max_length=512)]] = Field(default_factory=list, max_length=50, description="<security_context>Bounded command arguments for an approved local transport.</security_context>")
    auth_token: SecretStr | None = Field(default=None, max_length=8192, description="<security_context>Optional bearer token encrypted before persistence.</security_context>")

    @model_validator(mode="after")
    def validate_transport_fields(self):
        if self.server_type in {"sse", "streamable_http"} and not self.url:
            raise ValueError("mcp_remote_url_required")
        if self.server_type == "stdio" and not self.command:
            raise ValueError("mcp_stdio_command_required")
        return self
