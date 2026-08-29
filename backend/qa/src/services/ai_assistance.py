import httpx

from src.core.configuration import settings


async def request_impact_classification(project_id, change_set, candidates):
    evidence = [
        {
            "artifact_type": "requirement_change_set",
            "artifact_id": change_set["_id"],
            "artifact_version_id": change_set.get("to_version_id"),
            "authority": "PROJECT_BASELINE",
            "text": str(change_set.get("changes", [])),
        }
    ]
    evidence.extend(
        {
            "artifact_type": "test_case_version",
            "artifact_id": item.get("test_case_id"),
            "artifact_version_id": item.get("_id"),
            "authority": "PROJECT_BASELINE",
            "text": str(item.get("plain_text_projection", "")),
        }
        for item in candidates[:99]
    )
    request = {
        "capability": "impact_analysis",
        "project_id": project_id,
        "instruction": "Phân loại từng candidate thành STILL_VALID POTENTIALLY_AFFECTED NEEDS_UPDATE hoặc OBSOLETE và chỉ dùng artifact_version_id đã cung cấp",
        "evidence": evidence,
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{settings.AI_URL.rstrip('/')}/suy-luan/noi-bo/qa/ho-tro",
                headers={"X-Internal-Token": settings.SECRET_KEY},
                json=request,
            )
        response.raise_for_status()
        result = response.json()
        if result.get("capability") != "impact_analysis":
            raise ValueError("AI capability mismatch")
        return result
    except Exception as error:
        return {
            "capability": "impact_analysis",
            "suggestions": [],
            "evidence_refs": [item["artifact_version_id"] for item in evidence if item.get("artifact_version_id")],
            "confidence": 0,
            "warnings": ["AI_PROVIDER_UNAVAILABLE", "MANUAL_REVIEW_REQUIRED"],
            "status": "DEGRADED",
            "degraded_mode": "DEGRADED_AI",
            "model": {"provider": "deterministic-fallback", "model": "qa-rules-v2"},
            "error_type": type(error).__name__,
        }


def apply_ai_impact_suggestions(items, ai_result):
    allowed = {"STILL_VALID", "POTENTIALLY_AFFECTED", "NEEDS_UPDATE", "OBSOLETE"}
    by_version = {item["test_case_version_id"]: item for item in items}
    applied = []
    for suggestion in ai_result.get("suggestions", []):
        version_id = suggestion.get("test_case_version_id") or suggestion.get("artifact_version_id")
        classification = suggestion.get("classification")
        if version_id not in by_version or classification not in allowed:
            continue
        target = by_version[version_id]
        target["ai_classification"] = classification
        target["ai_confidence"] = max(0, min(1, float(suggestion.get("confidence", ai_result.get("confidence", 0)))))
        target["ai_reason"] = str(suggestion.get("reason") or "AI evidence classification")[:2000]
        target["evidence"].append(
            {
                "artifact_type": "ai_impact_classification",
                "artifact_version_id": version_id,
                "classification": classification,
                "confidence": target["ai_confidence"],
            }
        )
        if target["ai_confidence"] >= 0.7:
            target["classification"] = classification
            target["confidence"] = max(target["confidence"], target["ai_confidence"])
            target["reasons"].append(target["ai_reason"])
        applied.append(version_id)
    return applied
