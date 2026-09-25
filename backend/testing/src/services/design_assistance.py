import time
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Awaitable, Callable

from src.clients.ai_assistance import ai_assistance_client
from src.core.metrics import AI_GENERATION_LATENCY, AI_REQUESTS
from src.services.domain_policy import domain_policy


ASSISTANCE_POLICY = domain_policy("design_assistance")

stream_sink: ContextVar[Callable[[str], Awaitable[None]] | None] = ContextVar(
    "stream_sink", default=None
)


def ai_contract_metadata(result):
    model = result.get("model") if isinstance(result.get("model"), dict) else {}
    return {
        "capability": result.get("capability", ASSISTANCE_POLICY["unknown_value"]),
        "evidence_refs": result.get("evidence_refs", []),
        "reason_codes": result.get("reason_codes", []),
        "confidence": result.get("confidence", 0),
        "provider": result.get("provider")
        or model.get("provider")
        or ASSISTANCE_POLICY["unknown_value"],
        "model": model,
        "prompt_version": result.get("prompt_version")
        or model.get("prompt_version")
        or ASSISTANCE_POLICY["unknown_value"],
        "tool_schema_version": result.get("tool_schema_version")
        or model.get("tool_schema_version")
        or ASSISTANCE_POLICY["unknown_value"],
        "retrieval_version": result.get("retrieval_version")
        or model.get("retrieval_version")
        or ASSISTANCE_POLICY["unknown_value"],
        "created_at": result.get("created_at")
        or model.get("created_at")
        or datetime.now(timezone.utc).isoformat(),
        "status": result.get("status", ASSISTANCE_POLICY["degraded_status"]),
        "degraded_mode": result.get("degraded_mode"),
        "warnings": result.get("warnings", []),
    }


async def request_design_assistance(capability, project_id, instruction, evidence):
    started_at = time.perf_counter()
    try:
        sink = stream_sink.get()
        result = await ai_assistance_client.request(
            {
                "capability": capability,
                "project_id": project_id,
                "instruction": instruction,
                "evidence": evidence,
            },
            sink,
        )
        if result.get("capability") != capability:
            raise ValueError(ASSISTANCE_POLICY["capability_mismatch_error"])
        result["latency_ms"] = round((time.perf_counter() - started_at) * 1000, 3)
        AI_GENERATION_LATENCY.labels(capability).observe(result["latency_ms"] / 1000)
        outcome = (
            ASSISTANCE_POLICY["success_metric"]
            if result.get("status") == ASSISTANCE_POLICY["success_status"]
            and not result.get("degraded_mode")
            else ASSISTANCE_POLICY["degraded_metric"]
        )
        AI_REQUESTS.labels(capability, outcome).inc()
        return result
    except Exception as error:
        latency_ms = round((time.perf_counter() - started_at) * 1000, 3)
        AI_GENERATION_LATENCY.labels(capability).observe(latency_ms / 1000)
        AI_REQUESTS.labels(capability, ASSISTANCE_POLICY["degraded_metric"]).inc()
        return {
            "capability": capability,
            "suggestions": [],
            "evidence_refs": [
                str(item.get("artifact_version_id") or item.get("artifact_id"))
                for item in evidence
                if item.get("artifact_version_id") or item.get("artifact_id")
            ],
            "confidence": 0,
            "warnings": [
                ASSISTANCE_POLICY["provider_unavailable_code"],
                ASSISTANCE_POLICY["manual_review_code"],
            ],
            "reason_codes": [
                ASSISTANCE_POLICY["provider_unavailable_code"],
                ASSISTANCE_POLICY["manual_review_code"],
            ],
            "status": ASSISTANCE_POLICY["degraded_status"],
            "degraded_mode": ASSISTANCE_POLICY["degraded_mode"],
            "provider": ASSISTANCE_POLICY["unavailable_value"],
            "model": {
                "provider": ASSISTANCE_POLICY["unavailable_value"],
            },
            "prompt_version": ASSISTANCE_POLICY["unavailable_value"],
            "tool_schema_version": ASSISTANCE_POLICY["tool_schema_version"],
            "retrieval_version": ASSISTANCE_POLICY["retrieval_version"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "error_type": type(error).__name__,
            "latency_ms": latency_ms,
        }
