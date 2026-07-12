from src.core.infrastructure.mongo import mongo
from typing import Optional, Dict, Any, List

class MCPRepository:
    @classmethod
    async def insert_connector(cls, document: Dict[str, Any]) -> Any:
        return await mongo.insert_one("mcp_registry", document)

    @classmethod
    async def find_connector(cls, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return await mongo.find_one("mcp_registry", query)

    @classmethod
    def search_connectors(cls, query: Dict[str, Any], limit: int = 20):
        return mongo.find("mcp_registry", query).limit(limit)

    @classmethod
    async def update_connector(cls, filter_query: Dict[str, Any], update_data: Dict[str, Any]) -> Any:
        return await mongo.update_one("mcp_registry", filter_query, update_data)

    @classmethod
    async def delete_connector(cls, query: Dict[str, Any]) -> Any:
        return await mongo.delete_one("mcp_registry", query)
