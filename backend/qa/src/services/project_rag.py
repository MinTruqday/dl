import hashlib
import math
import re
from uuid import NAMESPACE_URL, uuid5

import httpx

from src.core.configuration import settings
from src.core.metrics import RAG_LATENCY


COLLECTION = "qa_project_knowledge"
SIZE = 128


def embedding(text):
    vector = [0.0] * SIZE
    for token in re.findall(r"[\w-]+", text.lower()):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % SIZE
        vector[index] += 1 if digest[4] % 2 else -1
    norm = math.sqrt(sum(value * value for value in vector)) or 1
    return [value / norm for value in vector]


async def ensure_collection(client):
    response = await client.get(f"/collections/{COLLECTION}")
    if response.status_code == 404:
        response = await client.put(f"/collections/{COLLECTION}", json={"vectors": {"size": SIZE, "distance": "Cosine"}})
    response.raise_for_status()


async def index_artifact(project_id, artifact_type, artifact_id, artifact_version_id, title, text, status, authority, version=None, module=""):
    if not text.strip():
        return False
    payload = {"project_id": project_id, "artifact_type": artifact_type, "artifact_id": artifact_id, "artifact_version_id": artifact_version_id, "module": module, "status": status, "authority": authority, "version": version, "chunk_index": 0, "title": title, "text": text[:12000]}
    point_id = str(uuid5(NAMESPACE_URL, f"{project_id}:{artifact_version_id}:0"))
    with RAG_LATENCY.labels("index").time():
        try:
            async with httpx.AsyncClient(base_url=settings.QDRANT_URL, timeout=10) as client:
                await ensure_collection(client)
                response = await client.put(f"/collections/{COLLECTION}/points?wait=true", json={"points": [{"id": point_id, "vector": embedding(f"{title} {text}"), "payload": payload}]})
                response.raise_for_status()
            return True
        except httpx.HTTPError:
            return False


async def search_project(project_id, query, artifact_types, limit):
    must = [{"key": "project_id", "match": {"value": project_id}}]
    if artifact_types:
        must.append({"key": "artifact_type", "match": {"any": artifact_types}})
    with RAG_LATENCY.labels("search").time():
        try:
            async with httpx.AsyncClient(base_url=settings.QDRANT_URL, timeout=10) as client:
                await ensure_collection(client)
                response = await client.post(f"/collections/{COLLECTION}/points/search", json={"vector": embedding(query), "filter": {"must": must}, "limit": limit, "with_payload": True, "score_threshold": 0.05})
                response.raise_for_status()
                points = response.json().get("result", [])
            return [{**item.get("payload", {}), "score": round(float(item.get("score", 0)), 4), "retrieval_source": "qdrant_dense"} for item in points]
        except httpx.HTTPError:
            return []
