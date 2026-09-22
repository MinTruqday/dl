from src.knowledge.graph.client import graph_client
from src.knowledge.graph.schema import ARTIFACT_LABELS, RELATIONSHIP_TYPES


class GraphRepository:
    async def ensure_schema(self):
        await graph_client.execute(
            "CREATE CONSTRAINT artifact_scope IF NOT EXISTS FOR (artifact:Artifact) REQUIRE artifact.scope_id IS UNIQUE"
        )

    async def upsert_artifact(self, project_id, label, artifact_id, properties=None):
        if label not in ARTIFACT_LABELS:
            raise ValueError("GRAPH_LABEL_INVALID")
        values = dict(properties or {})
        values.update(
            {
                "project_id": project_id,
                "artifact_id": artifact_id,
                "artifact_type": label,
                "scope_id": f"{project_id}:{label}:{artifact_id}",
            }
        )
        query = (
            f"MERGE (artifact:Artifact:{label} {{scope_id: $scope_id}}) "
            "SET artifact += $properties RETURN artifact.scope_id AS scope_id"
        )
        return await graph_client.execute(
            query,
            {"scope_id": values["scope_id"], "properties": values},
        )

    async def link(self, project_id, source_scope_id, relationship, target_scope_id):
        if relationship not in RELATIONSHIP_TYPES:
            raise ValueError("GRAPH_RELATIONSHIP_INVALID")
        query = (
            "MATCH (source:Artifact {scope_id: $source_scope_id, project_id: $project_id}) "
            "MATCH (target:Artifact {scope_id: $target_scope_id, project_id: $project_id}) "
            f"MERGE (source)-[relation:{relationship}]->(target) "
            "RETURN type(relation) AS relationship"
        )
        return await graph_client.execute(
            query,
            {
                "project_id": project_id,
                "source_scope_id": source_scope_id,
                "target_scope_id": target_scope_id,
            },
        )

    async def search(self, project_id, query, limit=20):
        statement = """
MATCH path=(source:Artifact {project_id: $project_id})-[*0..3]-(related:Artifact {project_id: $project_id})
WHERE toLower(coalesce(source.text, '') + ' ' + coalesce(source.title, '') + ' ' + coalesce(source.artifact_id, '')) CONTAINS toLower($query)
RETURN DISTINCT source.artifact_type AS artifact_type,
       source.artifact_id AS artifact_id,
       properties(source)[$artifact_version_property] AS artifact_version_id,
       coalesce(properties(source)[$authority_property], 'graph') AS authority,
       coalesce(source.text, source.title, '') AS text,
       [node IN nodes(path) | node.scope_id] AS relationship_path,
       length(path) AS distance
ORDER BY distance ASC
LIMIT $limit
"""
        return await graph_client.read(
            statement,
            {
                "project_id": project_id,
                "query": query,
                "limit": limit,
                "artifact_version_property": "artifact_version_id",
                "authority_property": "authority",
            },
        )


graph_repository = GraphRepository()
