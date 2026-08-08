from typing import Dict, List
from neo4j import AsyncGraphDatabase
from src.core.infrastructure.configuration import settings

class GraphStore:
    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )

    async def ensure_schema(self) -> None:
        await self.driver.execute_query(
            "CREATE CONSTRAINT entity_key IF NOT EXISTS FOR (entity:Entity) REQUIRE entity.key IS UNIQUE"
        )

    async def verify_connectivity(self) -> None:
        await self.driver.verify_connectivity()

    async def close(self) -> None:
        await self.driver.close()

    async def delete_document(self, document_id: str) -> None:
        await self.driver.execute_query(
            "MATCH (entity:Entity {document_id: $document_id}) DETACH DELETE entity",
            document_id=document_id,
        )

    async def replace_document(
        self,
        document_id: str,
        relations: List[Dict[str, str]],
    ) -> None:
        await self.delete_document(document_id)
        if not relations:
            return
        await self.driver.execute_query(
            """
            UNWIND $relations AS relation
            WITH relation,
                 trim(relation.source) AS source_name,
                 trim(relation.target) AS target_name,
                 toUpper(trim(relation.relation)) AS relation_name
            WHERE source_name <> '' AND target_name <> '' AND relation_name <> ''
            MERGE (source:Entity {key: $document_id + ':' + toLower(source_name)})
            SET source.name = source_name, source.document_id = $document_id
            MERGE (target:Entity {key: $document_id + ':' + toLower(target_name)})
            SET target.name = target_name, target.document_id = $document_id
            MERGE (source)-[edge:RELATED {
                document_id: $document_id,
                relation: relation_name
            }]->(target)
            """,
            document_id=document_id,
            relations=relations,
        )

    async def expand(
        self,
        document_ids: List[str],
        seed_query: str,
        limit: int = 20,
    ) -> List[Dict[str, str]]:
        tokens = [
            token.casefold()
            for token in seed_query.split()
            if len(token.strip()) > 3
        ][:12]
        records, _, _ = await self.driver.execute_query(
            """
            MATCH (source:Entity)-[edge:RELATED]->(target:Entity)
            WHERE edge.document_id IN $document_ids
              AND (
                size($tokens) = 0
                OR any(token IN $tokens WHERE
                    toLower(source.name) CONTAINS token
                    OR toLower(target.name) CONTAINS token
                )
              )
            RETURN source.name AS source,
                   edge.relation AS relation,
                   target.name AS target,
                   edge.document_id AS document_id
            LIMIT $limit
            """,
            document_ids=document_ids,
            tokens=tokens,
            limit=limit,
        )
        return [dict(record) for record in records]

graph_store = GraphStore()
