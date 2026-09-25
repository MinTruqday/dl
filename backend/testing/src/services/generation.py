import json
from collections import Counter
from fastapi import HTTPException
from pydantic import BaseModel, Field, ValidationError, field_validator

from src.core.common import plain_text
from src.domain.contracts import ScenarioCreate, TestCaseDraftCreate
from src.services.design_assistance import request_design_assistance
from src.services.domain_policy import domain_policy


GENERATION_POLICY = domain_policy("generation")


class GeneratedStep(BaseModel):
    action: str = Field(
        min_length=GENERATION_POLICY["minimum_text_length"],
        max_length=GENERATION_POLICY["maximum_text_length"],
    )
    expected: str = Field(
        min_length=GENERATION_POLICY["minimum_text_length"],
        max_length=GENERATION_POLICY["maximum_text_length"],
    )
    test_data: dict = Field(default_factory=dict)


class SecurityCandidate(BaseModel):
    category: str
    title: str = Field(
        min_length=GENERATION_POLICY["minimum_text_length"],
        max_length=GENERATION_POLICY["maximum_title_length"],
    )
    preconditions: list[str] = Field(
        min_length=1, max_length=GENERATION_POLICY["maximum_preconditions"]
    )
    action: str = Field(
        min_length=GENERATION_POLICY["minimum_text_length"],
        max_length=GENERATION_POLICY["maximum_text_length"],
    )
    expected: str = Field(
        min_length=GENERATION_POLICY["minimum_text_length"],
        max_length=GENERATION_POLICY["maximum_text_length"],
    )
    requirement_version_ids: list[str] = Field(
        default_factory=list, max_length=GENERATION_POLICY["maximum_list_length"]
    )

    @field_validator("category")
    @classmethod
    def validate_category(cls, value):
        if value not in GENERATION_POLICY["security_categories"]:
            raise ValueError(GENERATION_POLICY["invalid_categories_code"])
        return value


class PerformanceScenario(BaseModel):
    workload_type: str
    title: str = Field(
        min_length=GENERATION_POLICY["minimum_text_length"],
        max_length=GENERATION_POLICY["maximum_title_length"],
    )
    virtual_users: int = Field(ge=1, le=GENERATION_POLICY["maximum_virtual_users"])
    requests_per_second: float | None = Field(default=None, gt=0)
    duration_minutes: int = Field(ge=1, le=GENERATION_POLICY["maximum_duration_minutes"])
    ramp_pattern: str = Field(
        min_length=GENERATION_POLICY["minimum_text_length"],
        max_length=GENERATION_POLICY["maximum_short_text_length"],
    )
    actions: list[str] = Field(
        min_length=1, max_length=GENERATION_POLICY["maximum_steps"]
    )
    expected: str = Field(
        min_length=GENERATION_POLICY["minimum_text_length"],
        max_length=GENERATION_POLICY["maximum_text_length"],
    )

    @field_validator("workload_type")
    @classmethod
    def validate_workload_type(cls, value):
        if value not in GENERATION_POLICY["performance_workloads"]:
            raise ValueError(GENERATION_POLICY["invalid_categories_code"])
        return value


def validated_suggestions(result, schema):
    if result.get("status") != GENERATION_POLICY["success_status"] or result.get(
        "degraded_mode"
    ):
        raise HTTPException(
            503,
            detail={"code": GENERATION_POLICY["provider_unavailable_code"], "retryable": True},
        )
    try:
        items = result.get("suggestions")
        if (
            not isinstance(items, list)
            or not 1 <= len(items) <= GENERATION_POLICY["maximum_suggestions"]
        ):
            raise ValueError("invalid suggestion count")
        return [schema.model_validate(item).model_dump() for item in items]
    except (ValueError, TypeError, ValidationError) as error:
        raise HTTPException(
            502,
            detail={"code": GENERATION_POLICY["invalid_output_code"], "retryable": True},
        ) from error


class GeneratedCase(BaseModel):
    title: str = Field(
        min_length=GENERATION_POLICY["minimum_text_length"],
        max_length=GENERATION_POLICY["maximum_title_length"],
    )
    category: str
    objective: str = Field(
        min_length=GENERATION_POLICY["minimum_text_length"],
        max_length=GENERATION_POLICY["maximum_text_length"],
    )
    preconditions: str = Field(
        min_length=GENERATION_POLICY["minimum_text_length"],
        max_length=GENERATION_POLICY["maximum_text_length"],
    )
    steps: list[GeneratedStep] = Field(
        min_length=1, max_length=GENERATION_POLICY["maximum_steps"]
    )
    expected: str = Field(
        min_length=GENERATION_POLICY["minimum_text_length"],
        max_length=GENERATION_POLICY["maximum_text_length"],
    )
    acceptance_criterion_ids: list[str] = Field(default_factory=list)


def document(text):
    return {
        "type": "doc",
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
    }


async def generate_requirement_drafts(version, criteria, payload, scenario=False):
    categories = payload.categories or GENERATION_POLICY["default_categories"]
    allowed = ScenarioCreate.model_fields["category"].annotation.__args__
    if len(set(categories)) != len(categories) or any(item not in allowed for item in categories):
        raise HTTPException(422, detail={"code": GENERATION_POLICY["invalid_categories_code"]})
    if len(categories) * payload.count_per_category > GENERATION_POLICY["maximum_suggestions"]:
        raise HTTPException(422, detail={"code": GENERATION_POLICY["limit_exceeded_code"]})
    evidence = [
        {
            "artifact_type": GENERATION_POLICY["requirement_evidence_type"],
            "artifact_version_id": version["_id"],
            "text": version["plain_text_projection"],
        }
    ]
    evidence.extend(
        {
            "artifact_type": GENERATION_POLICY["criterion_evidence_type"],
            "artifact_version_id": item["_id"],
            "text": item.get("plain_text") or plain_text(item.get("content_doc", {})),
        }
        for item in criteria[: GENERATION_POLICY["maximum_criteria_evidence"]]
    )
    instruction = json.dumps(
        {
            "categories": categories,
            "count_per_category": payload.count_per_category,
            "user_instruction": payload.instruction,
        },
        ensure_ascii=False,
    )
    if len(instruction) > GENERATION_POLICY["maximum_instruction_length"]:
        raise HTTPException(
            422, detail={"code": GENERATION_POLICY["instruction_too_long_code"]}
        )
    result = await request_design_assistance(
        GENERATION_POLICY["scenario_capability"]
        if scenario
        else GENERATION_POLICY["test_capability"],
        version["project_id"],
        instruction,
        evidence,
    )
    if result.get("status") != GENERATION_POLICY["success_status"] or result.get(
        "degraded_mode"
    ):
        raise HTTPException(
            503,
            detail={"code": GENERATION_POLICY["provider_unavailable_code"], "retryable": True},
        )
    try:
        generated = [GeneratedCase.model_validate(item) for item in result.get("suggestions", [])]
        if Counter(item.category for item in generated) != Counter(
            {category: payload.count_per_category for category in categories}
        ):
            raise ValueError("category count mismatch")
        criterion_ids = {item["_id"] for item in criteria}
        drafts = []
        for item in generated:
            if not set(item.acceptance_criterion_ids) <= criterion_ids:
                raise ValueError("unknown evidence")
            common = {
                "title": item.title,
                "priority": version.get("priority", GENERATION_POLICY["default_priority"]),
                "risk": version.get("risk", GENERATION_POLICY["default_risk"]),
                "requirement_version_ids": [version["_id"]],
                "acceptance_criterion_ids": item.acceptance_criterion_ids,
                "origin": GENERATION_POLICY["generated_origin"],
            }
            if scenario:
                drafts.append(
                    ScenarioCreate(**common, category=item.category, objective=item.objective)
                )
            else:
                steps = [
                    {
                        "id": f"{GENERATION_POLICY['step_id_prefix']}{index}",
                        "order": index,
                        "action_doc": document(step.action),
                        "expected_doc": document(step.expected),
                        "test_data": step.test_data,
                    }
                    for index, step in enumerate(item.steps, 1)
                ]
                drafts.append(
                    TestCaseDraftCreate(
                        **common,
                        type=item.category,
                        objective_doc=document(item.objective),
                        preconditions_doc=document(item.preconditions),
                        steps=steps,
                        expected_result_doc=document(item.expected),
                        source_evidence=evidence,
                    )
                )
    except (ValueError, TypeError, ValidationError) as error:
        raise HTTPException(
            502,
            detail={"code": GENERATION_POLICY["invalid_output_code"], "retryable": True},
        ) from error
    return drafts, result
