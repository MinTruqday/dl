import json
from functools import lru_cache
from pathlib import Path

from src.knowledge.graph.repository import graph_repository


async def sync_artifact(project_id, artifact_type, artifact_id, properties=None):
    return await graph_repository.upsert_artifact(
        project_id,
        artifact_type,
        artifact_id,
        properties,
    )


async def sync_relationship(project_id, source_scope_id, relationship, target_scope_id):
    return await graph_repository.link(
        project_id,
        source_scope_id,
        relationship,
        target_scope_id,
    )


@lru_cache(maxsize=1)
def graph_mapping():
    path = Path(__file__).with_name("mapping.json")
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def scope_id(project_id, label, artifact_id):
    return f"{project_id}:{label}:{artifact_id}"


async def sync_indexed_artifact(project_id, artifact_type, artifact_id, version_id, properties):
    mapping = graph_mapping().get(artifact_type)
    if not mapping:
        return {"status": "SKIPPED", "reason_code": "GRAPH_MAPPING_UNAVAILABLE"}
    node_id = version_id or artifact_id
    await sync_artifact(project_id, mapping["label"], node_id, properties)
    parent_label = mapping.get("parent_label")
    relationship = mapping.get("parent_relationship")
    if parent_label and relationship and artifact_id != node_id:
        await sync_artifact(project_id, parent_label, artifact_id)
        await sync_relationship(
            project_id,
            scope_id(project_id, parent_label, artifact_id),
            relationship,
            scope_id(project_id, mapping["label"], node_id),
        )
        project_relationship = mapping.get("project_parent_relationship")
        if project_relationship:
            await sync_artifact(project_id, "Project", project_id)
            await sync_relationship(
                project_id,
                scope_id(project_id, "Project", project_id),
                project_relationship,
                scope_id(project_id, parent_label, artifact_id),
            )
    for relation in mapping.get("relationships", []):
        values = properties.get(relation["field"])
        if values is None:
            continue
        target_ids = values if isinstance(values, list) else [values]
        source_label = mapping["label"]
        source_id = node_id
        if relation["source"] == "parent" and parent_label:
            source_label = parent_label
            source_id = artifact_id
        for target_id in dict.fromkeys(str(value) for value in target_ids if value):
            await sync_artifact(project_id, relation["target_label"], target_id)
            source_scope = scope_id(project_id, source_label, source_id)
            target_scope = scope_id(project_id, relation["target_label"], target_id)
            if relation["source"] == "target":
                source_scope, target_scope = target_scope, source_scope
            await sync_relationship(
                project_id,
                source_scope,
                relation["relationship"],
                target_scope,
            )
    return {"status": "SYNCED", "scope_id": scope_id(project_id, mapping["label"], node_id)}
