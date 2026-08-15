from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError
from pydantic import BaseModel, Field

from src.repositories.mcp import MCPRepository
from src.schemas.mcp import RegisterServerRequest
from src.core.dependency import CurrentUser, get_current_user, verify_internal_token
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


router = APIRouter(prefix="/mcp")


@router.get("/presets")
async def list_mcp_presets(current_user: CurrentUser = Depends(get_current_user)):
    """Return only built-in connectors that pass a live MCP handshake and tool probe."""
    return {"status": "success", "presets": await MCPService.available_presets()}


@router.post("/presets/{preset_id}/connect")
async def connect_mcp_preset(
    preset_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Connect an immutable, server-owned preset after probing it again."""
    try:
        doc = MCPService.preset_connector(preset_id)
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": "mcp_preset_not_found"})
    existing = await MCPRepository.find_connector(
        {"owner_id": current_user.id, "preset_id": preset_id}
    )
    if existing:
        refreshed = MCPService.preset_connector(preset_id)
        refreshed["owner_id"] = current_user.id
        try:
            tools = await MCPService.probe_definition(refreshed)
        except Exception:
            await MCPRepository.update_connector(
                {"_id": existing["_id"], "owner_id": current_user.id},
                {
                    "$set": {
                        "is_connected": False,
                        "last_error": "mcp_preset_unavailable",
                    }
                },
            )
            raise HTTPException(
                status_code=503, detail={"code": "mcp_preset_unavailable"}
            )
        if not tools:
            await MCPRepository.update_connector(
                {"_id": existing["_id"], "owner_id": current_user.id},
                {
                    "$set": {
                        "is_connected": False,
                        "last_error": "mcp_preset_unavailable",
                    }
                },
            )
            raise HTTPException(
                status_code=503, detail={"code": "mcp_preset_unavailable"}
            )
        await MCPRepository.update_connector(
            {"_id": existing["_id"], "owner_id": current_user.id},
            {
                "$set": {
                    **refreshed,
                    "is_connected": True,
                    "tool_names": [tool["name"] for tool in tools],
                },
                "$unset": {"last_error": ""},
            },
        )
        return {
            "status": "success",
            "id": str(existing["_id"]),
            "already_connected": True,
            "tools": tools,
        }
    doc["owner_id"] = current_user.id
    try:
        tools = await MCPService.probe_definition(doc)
    except Exception:
        raise HTTPException(status_code=503, detail={"code": "mcp_preset_unavailable"})
    if not tools:
        raise HTTPException(status_code=503, detail={"code": "mcp_preset_unavailable"})
    doc["is_connected"] = True
    doc["tool_names"] = [tool["name"] for tool in tools]
    try:
        result = await MCPRepository.insert_connector(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail={"code": "mcp_connector_already_exists"})
    return {"status": "success", "id": str(result.inserted_id), "tools": tools}


@router.post("/servers")
async def register_mcp_server(
    req: RegisterServerRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Register an MCP server owned exclusively by the authenticated user"""
    if req.server_type == "stdio" and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail={"code": "mcp_stdio_requires_admin"})
    doc = req.model_dump()
    auth_token = doc.pop("auth_token", None)
    doc["owner_id"] = current_user.id
    if auth_token:
        doc["auth_secret"] = MCPService.seal_secret(
            auth_token.get_secret_value(), current_user.id
        )
    try:
        await MCPService.validate_connector(doc)
    except (ConnectionError, PermissionError, ValueError) as error:
        raise HTTPException(status_code=422, detail={"code": str(error)})
    doc["is_connected"] = False
    try:
        result = await MCPRepository.insert_connector(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail={"code": "mcp_connector_already_exists"})
    connector_id = str(result.inserted_id)
    try:
        tools = await MCPService.list_tools(connector_id, current_user.id)
    except Exception as error:
        await MCPRepository.delete_connector(
            {"_id": result.inserted_id, "owner_id": current_user.id}
        )
        code = str(error)
        if code in {
            "mcp_remote_endpoint_not_allowed",
            "mcp_remote_dns_resolution_failed",
            "mcp_remote_private_address_blocked",
            "mcp_remote_url_missing",
        }:
            raise HTTPException(status_code=422, detail={"code": code})
        raise HTTPException(
            status_code=502, detail={"code": "mcp_connection_failed", "id": connector_id}
        )
    if not tools:
        await MCPRepository.delete_connector(
            {"_id": result.inserted_id, "owner_id": current_user.id}
        )
        raise HTTPException(
            status_code=422, detail={"code": "mcp_server_has_no_tools"}
        )
    await MCPRepository.update_connector(
        {"_id": result.inserted_id},
        {
            "$set": {"is_connected": True, "tool_names": [tool["name"] for tool in tools]},
            "$unset": {"last_error": ""},
        },
    )
    return {"status": "success", "id": connector_id, "tools": tools}


@router.post("/servers/{server_id}/kiem-tra")
async def probe_mcp_server(
    server_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Probe one user-owned MCP server and persist its current connection and tool state"""
    from bson import ObjectId

    if not ObjectId.is_valid(server_id):
        raise HTTPException(status_code=404, detail={"code": "mcp_connector_not_found"})
    try:
        object_id = ObjectId(server_id)
        tools = await MCPService.list_tools(server_id, current_user.id)
        if not tools:
            raise ValueError("mcp_server_has_no_tools")
        await MCPRepository.update_connector(
            {"_id": object_id, "owner_id": current_user.id},
            {
                "$set": {"is_connected": True, "tool_names": [tool["name"] for tool in tools]},
                "$unset": {"last_error": ""},
            },
        )
        return {"status": "success", "tools": tools}
    except ValueError as error:
        if "object_id" in locals():
            await MCPRepository.update_connector(
                {"_id": object_id, "owner_id": current_user.id},
                {"$set": {"is_connected": False, "last_error": str(error)[:500]}},
            )
        raise HTTPException(status_code=422, detail={"code": str(error)})
    except Exception as error:
        if "object_id" in locals():
            await MCPRepository.update_connector(
                {"_id": object_id, "owner_id": current_user.id},
                {"$set": {"is_connected": False, "last_error": str(error)[:500]}},
            )
        raise HTTPException(status_code=502, detail={"code": "mcp_connection_failed"})


@router.get("/servers")
async def list_mcp_servers(current_user: CurrentUser = Depends(get_current_user)):
    """List MCP server connections owned by the authenticated user"""
    cursor = MCPRepository.search_connectors({"owner_id": current_user.id}, limit=100)
    docs = await cursor.to_list(length=None)
    for d in docs:
        d["_id"] = str(d["_id"])
        d.pop("auth_secret", None)
    return {"status": "success", "servers": docs}


@router.delete("/servers/{server_id}")
async def delete_mcp_server(
    server_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete one MCP server owned by the authenticated user"""
    from bson import ObjectId

    if not ObjectId.is_valid(server_id):
        raise HTTPException(status_code=404, detail={"code": "mcp_connector_not_found"})
    result = await MCPRepository.delete_connector(
        {"_id": ObjectId(server_id), "owner_id": current_user.id}
    )
    if result.deleted_count != 1:
        raise HTTPException(status_code=404, detail={"code": "mcp_connector_not_found"})
    return {"status": "success"}


@router.post("/callback", dependencies=[Depends(verify_internal_token)])
async def mcp_callback(req: CallbackRequest):
    """Publish an authenticated MCP tool result to its waiting task"""
    from src.core.infrastructure.redis import redis

    await redis.publish(f"tool_result:{req.task_id}", req.result)
    return {"status": "success"}
