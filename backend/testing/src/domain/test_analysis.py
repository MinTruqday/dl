import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class TestBasisRef(BaseModel):
    artifact_type: Literal[
        "REQUIREMENT_VERSION",
        "ACCEPTANCE_CRITERION",
        "API_OPERATION",
        "KNOWLEDGE_SOURCE",
        "BUSINESS_RULE",
        "RISK_RANKING",
        "DEFECT",
        "REGULATION",
    ]
    artifact_id: str = Field(min_length=1, max_length=200)
    artifact_version_id: str | None = Field(default=None, max_length=200)


class AnalysisFinding(BaseModel):
    finding_id: str = Field(min_length=1, max_length=200)
    finding_type: Literal[
        "AMBIGUITY",
        "OMISSION",
        "INCONSISTENCY",
        "CONTRADICTION",
        "UNTESTABLE",
        "MISSING_ACCEPTANCE_CRITERIA",
        "MISSING_ERROR_BEHAVIOR",
        "MISSING_PERMISSION_RULE",
        "MISSING_BOUNDARY",
        "MISSING_NON_FUNCTIONAL_CRITERIA",
    ]
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    source_ref: TestBasisRef
    description: str = Field(min_length=2, max_length=5000)
    suggestion: str = Field(default="", max_length=5000)
    status: Literal["OPEN", "RESOLVED", "ACCEPTED_RISK"] = "OPEN"
    resolved_by: str | None = Field(default=None, max_length=200)
    resolution_ref: str | None = Field(default=None, max_length=500)


class TestConditionCreate(BaseModel):
    condition_key: str | None = Field(default=None, max_length=80, pattern=r"^[A-Z][A-Z0-9_-]+$")
    title: str = Field(min_length=2, max_length=300)
    description_doc: dict[str, Any]
    basis_refs: list[TestBasisRef] = Field(min_length=1, max_length=200)
    coverage_item: str = Field(min_length=1, max_length=500)
    test_level: str = Field(min_length=1, max_length=100)
    test_type: str = Field(min_length=1, max_length=100)
    risk: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    priority: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    technique_candidates: list[str] = Field(default_factory=list, max_length=100)
    testability_status: Literal["TESTABLE", "CONDITIONALLY_TESTABLE", "UNTESTABLE"] = "TESTABLE"
    analysis_findings: list[AnalysisFinding] = Field(default_factory=list, max_length=200)
    origin: Literal["MANUAL", "AI_CANDIDATE_CONFIRMED"] = "MANUAL"
    ai_result_id: str | None = Field(default=None, max_length=200)

    @field_validator("description_doc")
    @classmethod
    def validate_description_doc(cls, value):
        if value.get("type") != "doc" or not isinstance(value.get("content", []), list):
            raise ValueError("Tiptap JSON không hợp lệ")
        return value


class TestConditionPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=2, max_length=300)
    description_doc: dict[str, Any] | None = None
    basis_refs: list[TestBasisRef] | None = Field(default=None, min_length=1, max_length=200)
    coverage_item: str | None = Field(default=None, min_length=1, max_length=500)
    test_level: str | None = Field(default=None, min_length=1, max_length=100)
    test_type: str | None = Field(default=None, min_length=1, max_length=100)
    risk: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] | None = None
    priority: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] | None = None
    technique_candidates: list[str] | None = Field(default=None, max_length=100)
    testability_status: Literal["TESTABLE", "CONDITIONALLY_TESTABLE", "UNTESTABLE"] | None = None
    analysis_findings: list[AnalysisFinding] | None = Field(default=None, max_length=200)


class TestConditionTransition(BaseModel):
    expected_revision: int = Field(ge=1)
    note: str = Field(default="", max_length=5000)


class FindingResolutionInput(BaseModel):
    expected_revision: int = Field(ge=1)
    status: Literal["RESOLVED", "ACCEPTED_RISK"]
    resolution_ref: str = Field(min_length=2, max_length=500)
    note: str = Field(min_length=2, max_length=5000)


class TestAnalysisAIInput(BaseModel):
    basis_refs: list[TestBasisRef] = Field(min_length=1, max_length=100)
    instruction: str = Field(default="", max_length=5000)
    idempotency_key: str = Field(min_length=8, max_length=200)


def condition_snapshot(value):
    return {
        "condition_id": value["_id"],
        "project_id": value["project_id"],
        "condition_key": value["condition_key"],
        **{field: value.get(field) for field in TestConditionCreate.model_fields},
        "basis_snapshots": value.get("basis_snapshots", []),
    }


def condition_hash(value):
    canonical = json.dumps(condition_snapshot(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
