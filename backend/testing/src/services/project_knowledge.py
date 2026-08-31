import httpx

from src.core.configuration import settings


async def index_artifact(
    project_id,
    artifact_type,
    artifact_id,
    artifact_version_id,
    title,
    text,
    status,
    authority,
    version=None,
    module="",
    **metadata,
):
    if not str(text or "").strip():
        return False
    payload = {
        "artifact_type": artifact_type,
        "artifact_id": artifact_id,
        "artifact_version_id": artifact_version_id,
        "title": title,
        "text": str(text)[:50000],
        "status": status,
        "authority": authority,
        "version": version,
        "module": module,
        "metadata": metadata,
    }
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{settings.AI_URL.rstrip('/')}/tri-thuc/du-an/{project_id}/doi-tuong",
                headers={"X-Internal-Token": settings.SECRET_KEY},
                json=payload,
            )
            response.raise_for_status()
        return True
    except httpx.HTTPError:
        return False


async def search_project_with_status(project_id, query, artifact_types, limit):
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{settings.AI_URL.rstrip('/')}/tri-thuc/du-an/{project_id}/tim-kiem",
                headers={"X-Internal-Token": settings.SECRET_KEY},
                json={"query": query, "artifact_types": artifact_types or [], "limit": limit},
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError:
        return {"items": [], "degraded_mode": "DEGRADED_KNOWLEDGE", "error_code": "KNOWLEDGE_UNAVAILABLE"}


async def search_project(project_id, query, artifact_types, limit):
    result = await search_project_with_status(project_id, query, artifact_types, limit)
    return result.get("items", [])
