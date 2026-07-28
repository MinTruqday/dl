from src.core.logic_logger import log_logic_execution
from src.repositories.mcp import MCPRepository
from typing import List, Dict, Any

class MCPService:
    @staticmethod
    @log_logic_execution
    async def search_registry(keyword: str) -> List[Dict[str, Any]]:
        query = {}
        if keyword:
            regex = {"$regex": keyword, "$options": "i"}
            query = {
                "$or": [
                    {"name": regex},
                    {"description": regex},
                    {"tags": regex}
                ]
            }
        cursor = MCPRepository.search_connectors(query, limit=10)
        connectors = await cursor.to_list(length=None)
        
        result = []
        for c in connectors:
            result.append({
                "directoryUuid": str(c.get("_id")),
                "name": c.get("name", ""),
                "description": c.get("description", ""),
                "is_connected": c.get("is_connected", False)
            })
        return result

    @staticmethod
    @log_logic_execution
    async def suggest_connector(directory_uuids: List[str]) -> Dict[str, Any]:
        connectors = []
        for uuid in directory_uuids:
            connectors.append({"directoryUuid": uuid})
        return {
            "type": "suggest_connectors",
            "connectors": connectors,
            "message_code": "connector_review_required",
        }

    @staticmethod
    @log_logic_execution
    async def execute_tool(directory_uuid: str, tool_name: str, arguments: dict) -> Any:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        from bson import ObjectId

        connector = await MCPRepository.find_connector({"_id": ObjectId(directory_uuid)})
        if not connector:
            raise LookupError("mcp_connector_not_found")

        server_type = connector.get("server_type", "stdio")
        if server_type == "stdio":
            from src.core.infrastructure.configuration import settings

            command = connector.get("command")
            args = connector.get("args", [])
            if not command:
                raise ValueError("mcp_stdio_command_missing")
            allowed_commands = {
                item.strip()
                for item in settings.MCP_ALLOWED_STDIO_COMMANDS.split(",")
                if item.strip()
            }
            if command not in allowed_commands:
                raise PermissionError("mcp_stdio_command_not_allowed")

            server_params = StdioServerParameters(command=command, args=args)
            try:
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(tool_name, arguments=arguments)
                        return result
            except Exception as exc:
                raise RuntimeError("mcp_stdio_execution_failed") from exc
        elif server_type == "sse":
            from urllib.parse import urlparse

            from mcp.client.sse import sse_client
            from src.core.infrastructure.configuration import settings

            url = connector.get("url")
            if not url:
                raise ValueError("mcp_sse_url_missing")
            parsed = urlparse(url)
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
                raise PermissionError("mcp_sse_endpoint_not_allowed")
            try:
                async with sse_client(url) as streams:
                    async with ClientSession(streams[0], streams[1]) as session:
                        await session.initialize()
                        result = await session.call_tool(tool_name, arguments=arguments)
                        return result
            except Exception as exc:
                raise RuntimeError("mcp_sse_execution_failed") from exc
        else:
            raise ValueError("mcp_server_type_unsupported")
