import time

import httpx

from src.core.configuration import settings
from src.core.metrics import AI_GENERATION_LATENCY, AI_REQUESTS


async def request_design_assistance(capability, project_id, instruction, evidence):
    started_at = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{settings.AI_URL.rstrip('/')}/suy-luan/noi-bo/kiem-thu/ho-tro",
                headers={"X-Internal-Token": settings.SECRET_KEY},
                json={
                    "capability": capability,
                    "project_id": project_id,
                    "instruction": instruction,
                    "evidence": evidence,
                },
            )
        response.raise_for_status()
        result = response.json()
        if result.get("capability") != capability:
            raise ValueError("AI capability mismatch")
        result["latency_ms"] = round((time.perf_counter() - started_at) * 1000, 3)
        AI_GENERATION_LATENCY.labels(capability).observe(result["latency_ms"] / 1000)
        AI_REQUESTS.labels(capability, "success").inc()
        return result
    except Exception as error:
        latency_ms = round((time.perf_counter() - started_at) * 1000, 3)
        AI_GENERATION_LATENCY.labels(capability).observe(latency_ms / 1000)
        AI_REQUESTS.labels(capability, "degraded").inc()
        return {
            "capability": capability,
            "suggestions": [],
            "evidence_refs": [
                str(item.get("artifact_version_id") or item.get("artifact_id"))
                for item in evidence
                if item.get("artifact_version_id") or item.get("artifact_id")
            ],
            "confidence": 0,
            "warnings": ["AI_PROVIDER_UNAVAILABLE", "MANUAL_REVIEW_REQUIRED"],
            "status": "DEGRADED",
            "degraded_mode": "DEGRADED_AI",
            "model": {
                "provider": "deterministic-fallback",
                "model": "qa-design-rules-v1",
                "prompt_version": "qa-design-v1",
                "tool_schema_version": "1",
                "retrieval_version": "project-filter-v1",
            },
            "error_type": type(error).__name__,
            "latency_ms": latency_ms,
        }
