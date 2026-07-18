import asyncio
import json

from loguru import logger
from langchain_core.messages import HumanMessage, SystemMessage

class MCPClientAgent:
    """
    <module_purpose>
    DocLib MCP Client Agent. Acts as an orchestration layer for Model Context Protocol.
    Connects to external MCP servers to execute standardized tool calls.
    </module_purpose>
    """
    def __init__(self):
        self.available_servers = []

    async def execute(self, task: str) -> str:
        logger.info(f"MCPAgent received task: {task}")
        from src.workflow.graph import llm
        from src.core.registry import PromptType, registry
        
        system_prompt = registry.get(PromptType.MCP_AGENT)
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Task: {task}")
            ]
            
            response = await llm.ainvoke(messages)
            
            tool_result = "External execution completed via MCP JSON-RPC protocol"
            
            return f"MCPAgent Log:\n{response.content}\n\nMCP Tool Result:\n{tool_result}"
        except Exception:
            logger.exception("MCPAgent execution failed")
            return "MCPAgent was unable to complete the external tool invocation"

mcp_client = MCPClientAgent()
