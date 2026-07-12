from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List
from pydantic import BaseModel

from src.repositories.mcp import MCPRepository
from src.core.logging_route import LoggingRoute

router = APIRouter(route_class=LoggingRoute, prefix="/mcp")

class RegisterServerRequest(BaseModel):
    name: str
    description: str
    server_type: str
    url: str = None
    command: str = None
    args: List[str] = []

@router.post("/servers")
async def register_mcp_server(req: RegisterServerRequest):
    doc = req.model_dump()
    doc["is_connected"] = True
    result = await MCPRepository.insert_connector(doc)
    return {"status": "success", "id": str(result.inserted_id)}

@router.get("/servers")
async def list_mcp_servers():
    cursor = MCPRepository.search_connectors({}, limit=100)
    docs = await cursor
    for d in docs:
        d["_id"] = str(d["_id"])
    return {"status": "success", "servers": docs}
