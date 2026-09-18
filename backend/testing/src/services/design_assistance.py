import time
from datetime import datetime, timezone

import httpx

from src.core.configuration import settings
from src.core.metrics import AI_GENERATION_LATENCY, AI_REQUESTS


def ai_contract_metadata(result):
    model = result.get("model") if isinstance(result.get("model"), dict) else {}
    return {
        "capability": result.get("capability", "unknown"),
        "evidence_refs": result.get("evidence_refs", []),
        "reason_codes": result.get("reason_codes", []),
        "confidence": result.get("confidence", 0),
        "provider": result.get("provider") or model.get("provider") or "unknown",
        "model": model,
        "prompt_version": result.get("prompt_version") or model.get("prompt_version") or "unknown",
        "tool_schema_version": result.get("tool_schema_version")
        or model.get("tool_schema_version")
        or "unknown",
        "retrieval_version": result.get("retrieval_version")
        or model.get("retrieval_version")
        or "unknown",
        "created_at": result.get("created_at")
        or model.get("created_at")
        or datetime.now(timezone.utc).isoformat(),
        "status": result.get("status", "DEGRADED"),
        "degraded_mode": result.get("degraded_mode"),
        "warnings": result.get("warnings", []),
    }


async def request_design_assistance(capability, project_id, instruction, evidence):
    started_at = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as client:
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
        outcome = (
            "success"
            if result.get("status") == "SUCCESS" and not result.get("degraded_mode")
            else "degraded"
        )
        AI_REQUESTS.labels(capability, outcome).inc()
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
            "reason_codes": ["AI_PROVIDER_UNAVAILABLE", "MANUAL_REVIEW_REQUIRED"],
            "status": "DEGRADED",
            "degraded_mode": "DEGRADED_AI",
            "provider": "deterministic-fallback",
            "model": {
                "provider": "deterministic-fallback",
                "model": "qa-design-rules-v1",
                "prompt_version": "qa-design-v1",
                "tool_schema_version": "1",
                "retrieval_version": "project-filter-v1",
            },
            "prompt_version": "qa-design-v1",
            "tool_schema_version": "1",
            "retrieval_version": "project-filter-v1",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "error_type": type(error).__name__,
            "latency_ms": latency_ms,
        }
