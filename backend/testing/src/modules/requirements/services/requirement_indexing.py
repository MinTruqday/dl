from fastapi import HTTPException

from src.core.common import now
from src.repositories.requirement_document import requirement_document_repository
from src.clients.project_knowledge import index_artifact





async def validate_requirement_sources(project_id, source_refs):
    references = [item for item in source_refs or [] if item.get("requirement_document_id")]
    if not references:
        return
    document_ids = list(dict.fromkeys(item["requirement_document_id"] for item in references))
    documents = await requirement_document_repository.list_by_ids(project_id, document_ids)
    by_id = {item["_id"]: item for item in documents}
    if set(by_id) != set(document_ids):
        raise HTTPException(
            status_code=422,
            detail={"code": 'CROSS_PROJECT_OR_MISSING_REQUIREMENT_DOCUMENT'},
        )
    for reference in references:
        expected_hash = reference.get("content_hash")
        if expected_hash and expected_hash != by_id[reference["requirement_document_id"]].get(
            "content_hash"
        ):
            raise HTTPException(
                status_code=422,
                detail={"code": 'REQUIREMENT_SOURCE_HASH_MISMATCH'},
            )


async def index_requirement_version(version):
    criteria = await requirement_document_repository.list_acceptance_criterion_ids(
        version["project_id"], version["_id"]
    )
    source_document_ids = list(
        dict.fromkeys(
            item.get("requirement_document_id")
            for item in version.get("source_refs", [])
            if item.get("requirement_document_id")
        )
    )
    indexed = await index_artifact(
        version["project_id"],
        'requirement_version',
        version["requirement_id"],
        version["_id"],
        version["title"],
        version.get("plain_text_projection", ""),
        version.get("status", 'DRAFT'),
        'APPROVED_SOURCE'
        if version.get("status") == 'BASELINED'
        else 'DRAFT',
        version.get("version"),
        acceptance_criterion_ids=[item["_id"] for item in criteria],
        source_document_ids=source_document_ids,
    )
    await requirement_document_repository.set_requirement_version_index_result(
        version["_id"],
        'READY'
        if indexed
        else 'FAILED',
        None if indexed else 'KNOWLEDGE_INDEX_FAILED',
        now(),
    )
    return indexed
