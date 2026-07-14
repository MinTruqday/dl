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
            "message": "Vui lòng xem xét và kết nối các ứng dụng bên thứ ba được đề xuất"
        }

    @staticmethod
    @log_logic_execution
    async def execute_tool(directory_uuid: str, tool_name: str, arguments: dict) -> Any:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        from bson import ObjectId

        connector = await MCPRepository.find_connector({"_id": ObjectId(directory_uuid)})
        if not connector:
            raise Exception("MCP Connector not found")

        server_type = connector.get("server_type", "stdio")
        if server_type == "stdio":
            command = connector.get("command")
            args = connector.get("args", [])
            if not command:
                raise Exception("Missing command for stdio MCP server")

            server_params = StdioServerParameters(command=command, args=args)
            try:
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(tool_name, arguments=arguments)
                        return result
            except Exception as e:
                raise Exception(f"Failed to execute MCP tool via stdio: {str(e)}")
        elif server_type == "sse":
            from mcp.client.sse import sse_client
            url = connector.get("url")
            if not url:
                raise Exception("Missing URL for sse MCP server")
            try:
                async with sse_client(url) as streams:
                    async with ClientSession(streams[0], streams[1]) as session:
                        await session.initialize()
                        result = await session.call_tool(tool_name, arguments=arguments)
                        return result
            except Exception as e:
                raise Exception(f"Failed to execute MCP tool via sse: {str(e)}")
        else:
            raise Exception("Unsupported MCP server type")
