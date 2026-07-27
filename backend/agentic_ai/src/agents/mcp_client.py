from loguru import logger

class MCPClientAgent:
    """
    <module_purpose>
    DocLib MCP Client Agent. Acts as an orchestration layer for Model Context Protocol.
    Connects to external MCP servers to execute standardized tool calls.
    </module_purpose>
    """
    def __init__(self):
        self.available_servers = []

    async def execute(
        self,
        directory_uuid: str,
        tool_name: str,
        arguments: dict,
    ):
        logger.info(f"MCPAgent invoking registered tool {tool_name}")
        try:
            from src.services.mcp import MCPService

            return await MCPService.execute_tool(
                directory_uuid,
                tool_name,
                arguments,
            )
        except Exception as exc:
            logger.exception("MCPAgent execution failed")
            raise RuntimeError("mcp_tool_execution_failed") from exc

mcp_client = MCPClientAgent()
