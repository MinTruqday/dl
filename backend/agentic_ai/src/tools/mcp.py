from typing import Annotated

from langchain_core.tools import tool
from pydantic import Field

from src.services.mcp import MCPService


@tool
async def search_mcp_connectors(
    keyword: Annotated[
        str,
        Field(
            min_length=1,
            max_length=128,
            description="Capability or service name to search in the approved MCP registry",
        ),
    ],
) -> list[dict]:
    """Search administrator approved MCP connectors by capability"""
    return await MCPService.search_registry(keyword)


@tool
async def suggest_mcp_connectors(
    directory_uuids: Annotated[
        list[str],
        Field(
            min_length=1,
            max_length=10,
            description="Opaque connector identifiers returned by search_mcp_connectors",
        ),
    ],
) -> dict:
    """Present approved MCP connectors for explicit user review"""
    return await MCPService.suggest_connector(directory_uuids)


@tool
async def execute_mcp_tool(
    directory_uuid: Annotated[
        str,
        Field(
            min_length=1,
            max_length=128,
            description="Approved connector identifier returned by search_mcp_connectors",
        ),
    ],
    tool_name: Annotated[
        str, Field(min_length=1, max_length=128, description="Exact MCP tool name")
    ],
    arguments: Annotated[
        dict, Field(description="JSON arguments validated by the selected MCP server")
    ],
) -> dict:
    """Execute one tool on an approved connected MCP server after user approval"""
    result = await MCPService.execute_tool(directory_uuid, tool_name, arguments)
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if hasattr(result, "dict"):
        return result.dict()
    return {"result": result}
