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
