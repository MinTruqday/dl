from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.repositories.mcp import MCPRepository
from src.core.logging_route import LoggingRoute
from src.schemas.mcp import RegisterServerRequest
from src.core.dependency import Role, require_role, verify_internal_token
from src.services.mcp import MCPService


class CallbackRequest(BaseModel):
    task_id: str = Field(
        min_length=1,
        max_length=128,
        description="<input_context>Waiting internal task identifier.</input_context>",
    )
    result: str = Field(
        max_length=1000000, description="<input_context>Serialized MCP tool result.</input_context>"
    )


router = APIRouter(route_class=LoggingRoute, prefix="/mcp")


@router.post("/servers", dependencies=[Depends(require_role([Role.ADMIN]))])
async def register_mcp_server(req: RegisterServerRequest):
    """Register an administrator managed MCP server connection"""
    from urllib.parse import urlparse

    from src.core.infrastructure.configuration import settings

    if req.server_type == "stdio":
        allowed_commands = {
            item.strip() for item in settings.MCP_ALLOWED_STDIO_COMMANDS.split(",") if item.strip()
        }
        if req.command not in allowed_commands:
            raise HTTPException(status_code=422, detail={"code": "mcp_stdio_command_not_allowed"})
    else:
        parsed = urlparse(req.url or "")
        allowed_hosts = {
            item.strip().lower()
            for item in settings.MCP_ALLOWED_SSE_HOSTS.split(",")
            if item.strip()
        }
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.hostname.lower() not in allowed_hosts
        ):
            raise HTTPException(status_code=422, detail={"code": "mcp_sse_endpoint_not_allowed"})
    doc = req.model_dump()
    doc["is_connected"] = False
    result = await MCPRepository.insert_connector(doc)
    connector_id = str(result.inserted_id)
    try:
        tools = await MCPService.list_tools(connector_id)
    except Exception as error:
        await MCPRepository.update_connector(
            {"_id": result.inserted_id},
            {"$set": {"is_connected": False, "last_error": str(error)[:500]}},
        )
        raise HTTPException(
            status_code=502, detail={"code": "mcp_connection_failed", "id": connector_id}
        )
    await MCPRepository.update_connector(
        {"_id": result.inserted_id},
        {
            "$set": {"is_connected": True, "tool_names": [tool["name"] for tool in tools]},
            "$unset": {"last_error": ""},
        },
    )
    return {"status": "success", "id": connector_id, "tools": tools}


@router.post("/servers/{server_id}/kiem-tra", dependencies=[Depends(require_role([Role.ADMIN]))])
async def probe_mcp_server(server_id: str):
    from bson import ObjectId

    try:
        object_id = ObjectId(server_id)
        tools = await MCPService.list_tools(server_id)
        await MCPRepository.update_connector(
            {"_id": object_id},
            {
                "$set": {"is_connected": True, "tool_names": [tool["name"] for tool in tools]},
                "$unset": {"last_error": ""},
            },
        )
        return {"status": "success", "tools": tools}
    except Exception as error:
        if "object_id" in locals():
            await MCPRepository.update_connector(
                {"_id": object_id},
                {"$set": {"is_connected": False, "last_error": str(error)[:500]}},
            )
        raise HTTPException(status_code=502, detail={"code": "mcp_connection_failed"})


@router.get("/servers", dependencies=[Depends(require_role([Role.ADMIN]))])
async def list_mcp_servers():
    """List registered MCP server connections and their status"""
    cursor = MCPRepository.search_connectors({}, limit=100)
    docs = await cursor.to_list(length=None)
    for d in docs:
        d["_id"] = str(d["_id"])
    return {"status": "success", "servers": docs}


@router.post("/callback", dependencies=[Depends(verify_internal_token)])
async def mcp_callback(req: CallbackRequest):
    """Publish an authenticated MCP tool result to its waiting task"""
    from src.core.infrastructure.redis import redis

    await redis.publish(f"tool_result:{req.task_id}", req.result)
    return {"status": "success"}
