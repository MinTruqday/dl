import asyncio
import base64
import hashlib
import ipaddress
import os
import shlex
import socket
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List
from urllib.parse import urlparse

from bson import ObjectId

from src.core.infrastructure.configuration import settings
from src.core.logic_logger import log_logic_execution
from src.repositories.mcp import MCPRepository


class MCPService:
    _preset_cache: tuple[float, list[dict[str, Any]]] = (0.0, [])
    _preset_lock = asyncio.Lock()

    @staticmethod
    def preset_specs() -> dict[str, dict[str, Any]]:
        root = settings.MCP_PRESET_ROOT.rstrip("/")
        return {
            "reqwise-figma": {
                "id": "reqwise-figma",
                "name": "Reqwise Figma",
                "description": "Đọc chỉnh sửa và kiểm tra bố cục trên tệp Figma đang mở",
                "server_type": "stdio",
                "command": "/usr/local/bin/node",
                "args": [f"{root}/reqwise/dist/server/index.js"],
                "source_url": "https://github.com/hoangpm96/reqwise-figma-mcp",
                "setup_note": "Cần mở Reqwise Figma MCP trong Figma Desktop để thao tác trên tệp",
            },
            "chrome-devtools": {
                "id": "chrome-devtools",
                "name": "Chrome DevTools",
                "description": "Mở trang tương tác đọc lỗi và kiểm tra hiệu năng",
                "server_type": "stdio",
                "command": "/usr/local/bin/node",
                "args": [
                    f"{root}/chrome/node_modules/chrome-devtools-mcp/build/src/bin/chrome-devtools-mcp.js",
                    "--headless=true",
                    "--isolated=true",
                    "--executablePath=/usr/bin/chromium",
                    "--chromeArg=--no-sandbox",
                    "--chromeArg=--disable-setuid-sandbox",
                    "--chromeArg=--disable-dev-shm-usage",
                    "--no-usage-statistics",
                    "--no-performance-crux",
                ],
                "source_url": "https://developer.chrome.com/blog/chrome-devtools-mcp",
                "setup_note": "Chạy trong hồ sơ Chromium tạm tách biệt với dữ liệu trình duyệt cá nhân",
            },
        }

    @staticmethod
    def preset_connector(preset_id: str) -> dict[str, Any]:
        preset = MCPService.preset_specs().get(preset_id)
        if not preset:
            raise LookupError("mcp_preset_not_found")
        return {
            "preset_id": preset_id,
            "name": preset["name"],
            "description": preset["description"],
            "server_type": preset["server_type"],
            "command": preset["command"],
            "args": list(preset["args"]),
        }

    @staticmethod
    def _is_trusted_preset(connector: dict) -> bool:
        preset_id = str(connector.get("preset_id") or "")
        if not preset_id:
            return False
        try:
            expected = MCPService.preset_connector(preset_id)
        except LookupError:
            return False
        return (
            connector.get("server_type") == expected["server_type"]
            and connector.get("command") == expected["command"]
            and list(connector.get("args") or []) == expected["args"]
        )

    @staticmethod
    def seal_secret(secret: str, owner_id: str) -> str:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        nonce = os.urandom(12)
        encrypted = AESGCM(key).encrypt(nonce, secret.encode(), owner_id.encode())
        return base64.urlsafe_b64encode(nonce + encrypted).decode()

    @staticmethod
    def _open_secret(value: str, owner_id: str) -> str:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        payload = base64.urlsafe_b64decode(value.encode())
        key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        return AESGCM(key).decrypt(payload[:12], payload[12:], owner_id.encode()).decode()

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
        allowed_hosts = MCPService._allowed_remote_hosts()
        if (
            parsed.scheme != "https"
            or not hostname
            or parsed.username
            or parsed.password
            or parsed.fragment
            or (allowed_hosts and hostname not in allowed_hosts)
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
            if MCPService._is_trusted_preset(connector):
                return
            if (command, *args) not in MCPService._allowed_stdio_specs():
                raise PermissionError("mcp_stdio_command_not_allowed")
            return
        if server_type in {"sse", "streamable_http"}:
            url = str(connector.get("url") or "")
            if not url:
                raise ValueError("mcp_remote_url_missing")
            await MCPService._validate_remote_url(url)
            return
        raise ValueError("mcp_server_type_unsupported")

    @staticmethod
    def _remote_headers(connector: dict) -> dict[str, str] | None:
        encrypted = str(connector.get("auth_secret") or "")
        if not encrypted:
            return None
        token = MCPService._open_secret(encrypted, str(connector["owner_id"]))
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
    async def probe_definition(connector: dict) -> list[dict]:
        async with MCPService._session(connector) as session:
            result = await asyncio.wait_for(session.list_tools(), timeout=25)
        return [
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema,
            }
            for tool in result.tools
        ]

    @staticmethod
    async def available_presets(force: bool = False) -> list[dict[str, Any]]:
        cached_at, cached = MCPService._preset_cache
        if not force and cached_at and time.monotonic() - cached_at < 300:
            return cached
        async with MCPService._preset_lock:
            cached_at, cached = MCPService._preset_cache
            if not force and cached_at and time.monotonic() - cached_at < 300:
                return cached
            verified: list[dict[str, Any]] = []
            for preset_id, metadata in MCPService.preset_specs().items():
                connector = MCPService.preset_connector(preset_id)
                try:
                    tools = await MCPService.probe_definition(connector)
                except Exception:
                    continue
                if not tools:
                    continue
                verified.append(
                    {
                        "id": preset_id,
                        "name": metadata["name"],
                        "description": metadata["description"],
                        "source_url": metadata["source_url"],
                        "setup_note": metadata["setup_note"],
                        "tool_count": len(tools),
                        "tool_names": [tool["name"] for tool in tools],
                        "verified": True,
                    }
                )
            MCPService._preset_cache = (time.monotonic(), verified)
            return verified

    @staticmethod
    async def _get_connector(directory_uuid: str, owner_id: str) -> dict:
        if not ObjectId.is_valid(directory_uuid):
            raise LookupError("mcp_connector_not_found")
        connector = await MCPRepository.find_connector(
            {"_id": ObjectId(directory_uuid), "owner_id": owner_id}
        )
        if not connector:
            raise LookupError("mcp_connector_not_found")
        return connector

    @staticmethod
    @log_logic_execution
    async def search_registry(keyword: str, owner_id: str) -> List[Dict[str, Any]]:
        query = {"is_connected": True, "owner_id": owner_id}
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
    async def suggest_connector(
        directory_uuids: List[str], owner_id: str
    ) -> Dict[str, Any]:
        object_ids = [ObjectId(value) for value in directory_uuids if ObjectId.is_valid(value)]
        cursor = MCPRepository.search_connectors(
            {"_id": {"$in": object_ids}, "owner_id": owner_id, "is_connected": True},
            limit=10,
        )
        owned = {str(item["_id"]) for item in await cursor.to_list(length=None)}
        return {
            "type": "suggest_connectors",
            "connectors": [
                {"directoryUuid": directory_uuid}
                for directory_uuid in directory_uuids
                if directory_uuid in owned
            ],
            "message_code": "connector_review_required",
        }

    @staticmethod
    @log_logic_execution
    async def execute_tool(
        directory_uuid: str, tool_name: str, arguments: dict, owner_id: str
    ) -> Any:
        connector = await MCPService._get_connector(directory_uuid, owner_id)
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
    async def list_tools(directory_uuid: str, owner_id: str) -> list[dict]:
        connector = await MCPService._get_connector(directory_uuid, owner_id)
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
