import json
from collections import Counter
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, Field, ValidationError

from src.core.common import plain_text
from src.domain.schemas import ScenarioCreate, TestCaseDraftCreate
from src.services.design_assistance import request_design_assistance


class GeneratedStep(BaseModel):
    action: str = Field(min_length=2, max_length=5000)
    expected: str = Field(min_length=2, max_length=5000)
    test_data: dict = Field(default_factory=dict)


class SecurityCandidate(BaseModel):
    category: Literal["authorization", "authentication", "input_validation", "session", "data_protection"]
    title: str = Field(min_length=2, max_length=300)
    preconditions: list[str] = Field(min_length=1, max_length=30)
    action: str = Field(min_length=2, max_length=5000)
    expected: str = Field(min_length=2, max_length=5000)
    requirement_version_ids: list[str] = Field(default_factory=list, max_length=100)


class PerformanceScenario(BaseModel):
    workload_type: Literal["baseline", "load", "stress", "spike", "soak"]
    title: str = Field(min_length=2, max_length=300)
    virtual_users: int = Field(ge=1, le=1000000)
    requests_per_second: float | None = Field(default=None, gt=0)
    duration_minutes: int = Field(ge=1, le=10080)
    ramp_pattern: str = Field(min_length=2, max_length=2000)
    actions: list[str] = Field(min_length=1, max_length=50)
    expected: str = Field(min_length=2, max_length=5000)


def validated_suggestions(result, schema):
    if result.get("status") != "SUCCESS" or result.get("degraded_mode"):
        raise HTTPException(503, detail={"code": "AI_PROVIDER_UNAVAILABLE", "retryable": True})
    try:
        items = result.get("suggestions")
        if not isinstance(items, list) or not 1 <= len(items) <= 100:
            raise ValueError("invalid suggestion count")
        return [schema.model_validate(item).model_dump() for item in items]
    except (ValueError, TypeError, ValidationError) as error:
        raise HTTPException(502, detail={"code": "AI_GENERATION_INVALID", "retryable": True}) from error


class GeneratedCase(BaseModel):
    title: str = Field(min_length=2, max_length=300)
    category: str
    objective: str = Field(min_length=2, max_length=5000)
    preconditions: str = Field(min_length=2, max_length=5000)
    steps: list[GeneratedStep] = Field(min_length=1, max_length=50)
    expected: str = Field(min_length=2, max_length=5000)
    acceptance_criterion_ids: list[str] = Field(default_factory=list)


def document(text):
    return {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]}


async def generate_requirement_drafts(version, criteria, payload, scenario=False):
    categories = payload.categories or ["happy_path", "negative", "boundary", "validation"]
    allowed = ScenarioCreate.model_fields["category"].annotation.__args__
    if len(set(categories)) != len(categories) or any(item not in allowed for item in categories):
        raise HTTPException(422, detail={"code": "INVALID_GENERATION_CATEGORIES"})
    if len(categories) * payload.count_per_category > 100:
        raise HTTPException(422, detail={"code": "GENERATION_LIMIT_EXCEEDED"})
    evidence = [{"artifact_type": "requirement_version", "artifact_version_id": version["_id"], "text": version["plain_text_projection"]}]
    evidence.extend({"artifact_type": "acceptance_criterion", "artifact_version_id": item["_id"], "text": item.get("plain_text") or plain_text(item.get("content_doc", {}))} for item in criteria[:99])
    instruction = json.dumps({"task": "Sinh các tình huống cụ thể bằng tiếng Việt từ bằng chứng với dữ liệu đầu vào và kết quả có thể kiểm chứng không dùng câu mẫu chung chung", "categories": categories, "count_per_category": payload.count_per_category, "user_instruction": payload.instruction, "suggestion_schema": GeneratedCase.model_json_schema()}, ensure_ascii=False)
    if len(instruction) > 5000:
        raise HTTPException(422, detail={"code": "GENERATION_INSTRUCTION_TOO_LONG"})
    result = await request_design_assistance("scenario_generation" if scenario else "test_generation", version["project_id"], instruction, evidence)
    if result.get("status") != "SUCCESS" or result.get("degraded_mode"):
        raise HTTPException(503, detail={"code": "AI_PROVIDER_UNAVAILABLE", "retryable": True})
    try:
        generated = [GeneratedCase.model_validate(item) for item in result.get("suggestions", [])]
        if Counter(item.category for item in generated) != Counter({category: payload.count_per_category for category in categories}):
            raise ValueError("category count mismatch")
        criterion_ids = {item["_id"] for item in criteria}
        drafts = []
        for item in generated:
            if not set(item.acceptance_criterion_ids) <= criterion_ids:
                raise ValueError("unknown evidence")
            common = {"title": item.title, "priority": version.get("priority", "medium"), "risk": version.get("risk", "medium"), "requirement_version_ids": [version["_id"]], "acceptance_criterion_ids": item.acceptance_criterion_ids, "origin": "ai_generated"}
            if scenario:
                drafts.append(ScenarioCreate(**common, category=item.category, objective=item.objective))
            else:
                steps = [{"id": f"step-{index}", "order": index, "action_doc": document(step.action), "expected_doc": document(step.expected), "test_data": step.test_data} for index, step in enumerate(item.steps, 1)]
                drafts.append(TestCaseDraftCreate(**common, type=item.category, objective_doc=document(item.objective), preconditions_doc=document(item.preconditions), steps=steps, expected_result_doc=document(item.expected), source_evidence=evidence))
    except (ValueError, TypeError, ValidationError) as error:
        raise HTTPException(502, detail={"code": "AI_GENERATION_INVALID", "retryable": True}) from error
    return drafts, result
