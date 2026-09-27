from src.knowledge.graph.repository import graph_repository


def graph_label(artifact_type):
    return "".join(part.capitalize() for part in str(artifact_type).split("_"))


def scope_id(project_id, artifact_type, artifact_id):
    return f"{project_id}:{graph_label(artifact_type)}:{artifact_id}"


def reference_ids(properties, artifact_id):
    values = []
    for field, value in properties.items():
        if not str(field).endswith(("_id", "_ids")):
            continue
        candidates = value if isinstance(value, list) else [value]
        values.extend(str(candidate) for candidate in candidates if candidate)
    return [value for value in dict.fromkeys(values) if value != str(artifact_id)]


async def sync_indexed_artifact(project_id, artifact_type, artifact_id, version_id, properties):
    node_id = str(version_id or artifact_id)
    node_scope_id = scope_id(project_id, artifact_type, node_id)
    references = reference_ids(properties, node_id)
    await graph_repository.upsert_artifact(
        project_id,
        artifact_type,
        node_id,
        node_scope_id,
        properties,
        references,
    )
    if artifact_id and str(artifact_id) != node_id:
        parent_type = str(artifact_type).removesuffix("_version")
        parent_scope_id = scope_id(project_id, parent_type, artifact_id)
        await graph_repository.upsert_artifact(
            project_id,
            parent_type,
            str(artifact_id),
            parent_scope_id,
        )
        await graph_repository.link(project_id, parent_scope_id, node_id)
    await graph_repository.reconcile(
        project_id,
        node_scope_id,
        [node_id],
    )
    return {"status": "SYNCED", "scope_id": node_scope_id}
