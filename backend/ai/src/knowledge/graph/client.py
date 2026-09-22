from neo4j import AsyncGraphDatabase

from src.core.infrastructure.configuration import settings


class GraphClient:
    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )

    async def ready(self):
        await self.driver.verify_connectivity()
        return True

    async def close(self):
        await self.driver.close()

    async def execute(self, query, parameters=None):
        records, _, _ = await self.driver.execute_query(
            query,
            parameters_=(parameters or {}),
            routing_="w",
            database_="neo4j",
        )
        return [record.data() for record in records]

    async def read(self, query, parameters=None):
        records, _, _ = await self.driver.execute_query(
            query,
            parameters_=(parameters or {}),
            routing_="r",
            database_="neo4j",
        )
        return [record.data() for record in records]


graph_client = GraphClient()
