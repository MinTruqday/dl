import json
from datetime import datetime, timezone

from fastapi import HTTPException

from src.core.infrastructure.configuration import settings
from src.core.security.guardrails import guardrails_engine
from src.prompts.testing import build_testing_prompt, capability_token_budget
from src.runtime.output import normalize_narrative_payload
from src.schemas.inference import (
    AutomationScriptOutput,
    CausalHypothesesOutput,
    CompletionReportNarrativeOutput,
    GeneratedCasesOutput,
    ImpactClassificationOutput,
    LessonsLearnedClustersOutput,
    PerformanceSuggestionsOutput,
    ProjectQuestionOutput,
    RequirementQualityOutput,
    SecuritySuggestionsOutput,
    StatusReportNarrativeOutput,
    TestConditionSuggestionsOutput,
    TestingAssistanceRequest,
    TestingAssistanceResult,
)
from src.services.inference import chat, structured


SCHEMAS = {
    "project_question": ProjectQuestionOutput,
    "requirement_quality_analysis": RequirementQualityOutput,
    "scenario_generation": GeneratedCasesOutput,
    "test_generation": GeneratedCasesOutput,
    "impact_analysis": ImpactClassificationOutput,
    "security_test_generation": SecuritySuggestionsOutput,
    "performance_plan_generation": PerformanceSuggestionsOutput,
    "automation_script_generation": AutomationScriptOutput,
    "test_condition_generation": TestConditionSuggestionsOutput,
    "causal_analysis": CausalHypothesesOutput,
    "status_report_narrative": StatusReportNarrativeOutput,
    "completion_report_narrative": CompletionReportNarrativeOutput,
    "lessons_learned_clustering": LessonsLearnedClustersOutput,
}

def evidence_text(evidence, compact=False):
    values = []
    for item in evidence:
        reference = item.get("artifact_version_id") or item.get("artifact_id")
        if compact:
            values.append(f"[{reference}] {str(item.get('text', ''))[:4000]}")
            continue
        metadata = {
            key: item.get(key)
            for key in ("artifact_type", "artifact_id", "artifact_version_id", "authority")
            if item.get(key) is not None
        }
        values.extend(
            (json.dumps(metadata, ensure_ascii=False, default=str), str(item.get("text", ""))[:4000])
        )
    return "\n".join(values)


def evidence_reference_ids(evidence):
    return [
        str(item.get("artifact_version_id") or item.get("artifact_id"))
        for item in evidence
        if item.get("artifact_version_id") or item.get("artifact_id")
    ]


def nested_values(value, key_name):
    values = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == key_name and isinstance(item, list):
                values.extend(str(entry) for entry in item)
            else:
                values.extend(nested_values(item, key_name))
    elif isinstance(value, list):
        for item in value:
            values.extend(nested_values(item, key_name))
    return values


async def generate_testing_assistance(req: TestingAssistanceRequest):
    evidence = [
        {
            "artifact_type": item.get("artifact_type"),
            "artifact_id": item.get("artifact_id"),
            "artifact_version_id": item.get("artifact_version_id"),
            "authority": item.get("authority"),
            "text": str(item.get("text", ""))[:4000],
        }
        for item in req.evidence
    ]
    source_text = evidence_text(
        evidence,
        compact=req.capability in {"project_question", "requirement_quality_analysis"},
    )
    inspected = guardrails_engine.inspect_input(source_text)
    if not inspected.get("is_safe", False):
        raise HTTPException(status_code=422, detail={"code": "qa_evidence_unsafe"})
    allowed_evidence_refs = evidence_reference_ids(evidence)
    prompt = build_testing_prompt(
        req.capability,
        req.project_id,
        req.instruction,
        str(inspected.get("sanitized_text") or ""),
        allowed_evidence_refs,
    )
    model = {
        "provider": "primary",
        "model": settings.LLM_MODEL,
        "prompt_version": "testing_assistance",
        "tool_schema_version": "testing_assistance",
        "retrieval_version": "project_evidence",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        if req.capability == "project_question":
            answer = await chat(
                [{"role": "user", "content": prompt}],
                max_tokens=capability_token_budget(req.capability),
                temperature=0.1,
                attempts=1,
                timeout_seconds=settings.MODEL_TIMEOUT_SECONDS,
            )
            output_check = guardrails_engine.inspect_output(answer)
            if not output_check.get("is_safe", False):
                raise ValueError("AI_OUTPUT_UNSAFE")
            generated = ProjectQuestionOutput(
                capability="project_question",
                answer=str(output_check.get("sanitized_text") or "").strip().rstrip(" .!?…"),
                evidence_refs=allowed_evidence_refs,
                confidence=0.8,
                warnings=[],
            )
        else:
            generated = await structured(
                prompt,
                SCHEMAS[req.capability],
                max_tokens=capability_token_budget(req.capability),
                timeout_seconds=settings.MODEL_TIMEOUT_SECONDS,
                provider_schema=req.capability != "test_condition_generation",
            )
        generated_data = normalize_narrative_payload(generated.model_dump())
        unknown_refs = sorted(
            set(nested_values(generated_data, "evidence_refs")) - set(allowed_evidence_refs)
        )
        if unknown_refs:
            raise ValueError("AI_EVIDENCE_REF_UNKNOWN")
        if req.capability == "test_condition_generation":
            generated_data["suggestions"] = generated_data.pop("condition_candidates")
        generated_data.update(
            {
                "status": "SUCCESS",
                "degraded_mode": None,
                "provider": model["provider"],
                "model": model,
                "prompt_version": model["prompt_version"],
                "tool_schema_version": model["tool_schema_version"],
                "retrieval_version": model["retrieval_version"],
                "created_at": model["created_at"],
            }
        )
        result = TestingAssistanceResult(**generated_data)
    except Exception as error:
        output_invalid = type(error).__name__ in {
            "StructuredOutputError",
            "ValidationError",
            "ValueError",
        }
        failure_code = "AI_OUTPUT_INVALID" if output_invalid else "AI_PROVIDER_UNAVAILABLE"
        result = TestingAssistanceResult(
            capability=req.capability,
            suggestions=[],
            evidence_refs=evidence_reference_ids(req.evidence),
            confidence=0,
            warnings=[failure_code, "MANUAL_REVIEW_REQUIRED"],
            status="DEGRADED",
            degraded_mode="DEGRADED_AI",
            provider="unavailable",
            model={**model, "provider": "unavailable"},
            prompt_version=model["prompt_version"],
            tool_schema_version=model["tool_schema_version"],
            retrieval_version=model["retrieval_version"],
            created_at=model["created_at"],
            reason_codes=[failure_code, "MANUAL_REVIEW_REQUIRED"],
            answer="Không thể tạo câu trả lời có căn cứ khi nhà cung cấp AI chưa sẵn sàng",
        )
    if result.capability != req.capability:
        raise HTTPException(status_code=502, detail={"code": "qa_capability_mismatch"})
    if not result.evidence_refs:
        result.evidence_refs = evidence_reference_ids(req.evidence)
    if not result.reason_codes:
        result.reason_codes = (
            nested_values(result.model_dump(), "reason_codes")[:100]
            or [
                str(item.get("reason_code") or item.get("action") or "EVIDENCE_REVIEW")
                for item in result.suggestions
            ][:100]
        )
    result.workflow = {
        "request_id": f"qa-{datetime.now(timezone.utc).timestamp()}",
        "project_id": req.project_id,
        "intent": req.capability,
        "phases": [
            "OBSERVE_EVIDENCE",
            "REASON_AND_PLAN",
            "ACT_VALIDATE_PROPOSAL",
            "OBSERVE_VALIDATION",
        ],
        "evidence_count": len(evidence),
        "candidate_count": len(result.suggestions),
        "confidence": result.confidence,
        "degraded_flags": result.warnings if result.status == "DEGRADED" else [],
        "approval_required": bool(result.suggestions),
        "hidden_reasoning_stored": False,
    }
    return result
