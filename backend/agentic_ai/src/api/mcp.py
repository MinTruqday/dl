from fastapi import APIRouter, Depends
from typing import Any, Dict, List
from pydantic import BaseModel

from src.repositories.mcp import MCPRepository
from src.core.logging_route import LoggingRoute
from src.schemas.mcp import RegisterServerRequest
from src.core.dependency import Role, require_role, verify_internal_token

class CallbackRequest(BaseModel):
    task_id: str
    result: str

router = APIRouter(route_class=LoggingRoute, prefix="/mcp")

@router.post(
    "/servers",
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def register_mcp_server(req: RegisterServerRequest):
    doc = req.model_dump()
    doc["is_connected"] = True
    result = await MCPRepository.insert_connector(doc)
    return {"status": "success", "id": str(result.inserted_id)}

@router.get(
    "/servers",
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def list_mcp_servers():
    cursor = MCPRepository.search_connectors({}, limit=100)
    docs = await cursor.to_list(length=None)
    for d in docs:
        d["_id"] = str(d["_id"])
    return {"status": "success", "servers": docs}

@router.post(
    "/callback",
    dependencies=[Depends(verify_internal_token)],
)
async def mcp_callback(req: CallbackRequest):
    from src.core.infrastructure.redis import redis
    await redis.publish(f"tool_result:{req.task_id}", req.result)
    return {"status": "success"}
