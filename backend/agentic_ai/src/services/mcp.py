import asyncio
import ipaddress
import json
import os
import shlex
import socket
from contextlib import asynccontextmanager
from typing import Any, Dict, List
from urllib.parse import urlparse

from bson import ObjectId

from src.core.infrastructure.configuration import settings
from src.core.logic_logger import log_logic_execution
from src.repositories.mcp import MCPRepository


class MCPService:
    @staticmethod
    async def bootstrap_connectors() -> list[dict[str, Any]]:
        raw = settings.MCP_BOOTSTRAP_CONNECTORS.strip()
        if not raw:
            return []
        payload = json.loads(raw)
        if not isinstance(payload, list) or len(payload) > 20:
            raise ValueError("mcp_bootstrap_configuration_invalid")
        from src.schemas.mcp import RegisterServerRequest

        statuses = []
        for item in payload:
            connector = RegisterServerRequest.model_validate(item).model_dump()
            await MCPService.validate_connector(connector)
            existing = await MCPRepository.find_connector({"name": connector["name"]})
            if existing:
                connector_id = str(existing["_id"])
                await MCPRepository.update_connector(
                    {"_id": existing["_id"]},
                    {"$set": {**connector, "is_connected": False}},
                )
            else:
                result = await MCPRepository.insert_connector(
                    {**connector, "is_connected": False}
                )
                connector_id = str(result.inserted_id)
            try:
                tools = await asyncio.wait_for(
                    MCPService.list_tools(connector_id), timeout=30
                )
                await MCPRepository.update_connector(
                    {"_id": ObjectId(connector_id)},
                    {
                        "$set": {
                            "is_connected": True,
                            "tool_names": [tool["name"] for tool in tools],
                        },
                        "$unset": {"last_error": ""},
                    },
                )
                statuses.append({"id": connector_id, "is_connected": True})
            except Exception as exc:
                await MCPRepository.update_connector(
                    {"_id": ObjectId(connector_id)},
                    {
                        "$set": {
                            "is_connected": False,
                            "last_error": str(exc)[:500],
                        }
                    },
                )
                statuses.append({"id": connector_id, "is_connected": False})
        return statuses

    @staticmethod
    def _allowed_remote_hosts() -> set[str]:
        return {
            item.strip().lower().rstrip(".")
            for item in settings.MCP_ALLOWED_REMOTE_HOSTS.split(",")
            if item.strip()
        }

    @staticmethod
    def _allowed_stdio_specs() -> set[tuple[str, ...]]:
        specs = set()
        for item in settings.MCP_ALLOWED_STDIO_COMMANDS.split(","):
            if item.strip():
                parts = tuple(shlex.split(item.strip()))
                if parts:
                    specs.add(parts)
        return specs

    @staticmethod
    async def _validate_remote_url(url: str) -> None:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower().rstrip(".")
        if (
            parsed.scheme != "https"
            or not hostname
            or parsed.username
            or parsed.password
            or parsed.fragment
            or hostname not in MCPService._allowed_remote_hosts()
            or parsed.port not in {None, 443}
        ):
            raise PermissionError("mcp_remote_endpoint_not_allowed")
        if settings.MCP_ALLOW_PRIVATE_NETWORKS:
            return
        addresses = []
        resolution_error = None
        for attempt in range(3):
            try:
                addresses = await asyncio.to_thread(
                    socket.getaddrinfo, hostname, parsed.port or 443, type=socket.SOCK_STREAM
                )
                break
            except socket.gaierror as exc:
                resolution_error = exc
                if attempt < 2:
                    await asyncio.sleep(0.2 * (attempt + 1))
        if not addresses:
            raise ConnectionError("mcp_remote_dns_resolution_failed") from resolution_error
        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if not ip.is_global:
                raise PermissionError("mcp_remote_private_address_blocked")

    @staticmethod
    async def validate_connector(connector: dict) -> None:
        server_type = connector.get("server_type", "stdio")
        if server_type == "stdio":
            command = str(connector.get("command") or "")
            args = tuple(str(item) for item in connector.get("args", []))
            if (command, *args) not in MCPService._allowed_stdio_specs():
                raise PermissionError("mcp_stdio_command_not_allowed")
            return
        if server_type in {"sse", "streamable_http"}:
            url = str(connector.get("url") or "")
            if not url:
                raise ValueError("mcp_remote_url_missing")
            await MCPService._validate_remote_url(url)
            auth_env = connector.get("auth_env")
            if auth_env and not os.environ.get(str(auth_env)):
                raise PermissionError("mcp_remote_authentication_missing")
            return
        raise ValueError("mcp_server_type_unsupported")

    @staticmethod
    def _remote_headers(connector: dict) -> dict[str, str] | None:
        auth_env = connector.get("auth_env")
        if not auth_env:
            return None
        token = os.environ.get(str(auth_env), "")
        if not token:
            raise PermissionError("mcp_remote_authentication_missing")
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    @asynccontextmanager
    async def _session(connector: dict):
        from mcp import ClientSession, StdioServerParameters

        await MCPService.validate_connector(connector)
        server_type = connector.get("server_type", "stdio")
        if server_type == "stdio":
            from mcp.client.stdio import stdio_client

            parameters = StdioServerParameters(
                command=connector["command"], args=connector.get("args", [])
            )
            async with stdio_client(parameters) as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    await session.initialize()
                    yield session
            return
        headers = MCPService._remote_headers(connector)
        if server_type == "sse":
            from mcp.client.sse import sse_client

            async with sse_client(
                connector["url"], headers=headers, timeout=15, sse_read_timeout=120
            ) as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    await session.initialize()
                    yield session
            return
        from mcp.client.streamable_http import streamablehttp_client

        async with streamablehttp_client(
            connector["url"], headers=headers, timeout=15, sse_read_timeout=120
        ) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                yield session

    @staticmethod
    async def _get_connector(directory_uuid: str) -> dict:
        if not ObjectId.is_valid(directory_uuid):
            raise LookupError("mcp_connector_not_found")
        connector = await MCPRepository.find_connector({"_id": ObjectId(directory_uuid)})
        if not connector:
            raise LookupError("mcp_connector_not_found")
        return connector

    @staticmethod
    @log_logic_execution
    async def search_registry(keyword: str) -> List[Dict[str, Any]]:
        query = {"is_connected": True}
        if keyword:
            regex = {"$regex": keyword, "$options": "i"}
            query["$or"] = [{"name": regex}, {"description": regex}, {"tags": regex}]
        cursor = MCPRepository.search_connectors(query, limit=10)
        connectors = await cursor.to_list(length=None)
        return [
            {
                "directoryUuid": str(connector.get("_id")),
                "name": connector.get("name", ""),
                "description": connector.get("description", ""),
                "is_connected": connector.get("is_connected", False),
                "tool_names": connector.get("tool_names", []),
            }
            for connector in connectors
        ]

    @staticmethod
    @log_logic_execution
    async def suggest_connector(directory_uuids: List[str]) -> Dict[str, Any]:
        return {
            "type": "suggest_connectors",
            "connectors": [
                {"directoryUuid": directory_uuid} for directory_uuid in directory_uuids
            ],
            "message_code": "connector_review_required",
        }

    @staticmethod
    @log_logic_execution
    async def execute_tool(directory_uuid: str, tool_name: str, arguments: dict) -> Any:
        connector = await MCPService._get_connector(directory_uuid)
        if not connector.get("is_connected", False):
            raise ConnectionError("mcp_connector_not_connected")
        known_tools = set(connector.get("tool_names", []))
        if tool_name not in known_tools:
            raise PermissionError("mcp_tool_not_registered")
        try:
            async with MCPService._session(connector) as session:
                return await session.call_tool(tool_name, arguments=arguments)
        except (LookupError, PermissionError, ValueError):
            raise
        except Exception as exc:
            raise RuntimeError("mcp_tool_execution_failed") from exc

    @staticmethod
    @log_logic_execution
    async def list_tools(directory_uuid: str) -> list[dict]:
        connector = await MCPService._get_connector(directory_uuid)
        try:
            async with MCPService._session(connector) as session:
                result = await session.list_tools()
        except (LookupError, PermissionError, ValueError):
            raise
        except Exception as exc:
            raise RuntimeError("mcp_connection_failed") from exc
        return [
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema,
            }
            for tool in result.tools
        ]
