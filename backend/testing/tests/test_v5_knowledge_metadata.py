from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.domain.schemas import KnowledgeSourceCreate, RequirementDocumentPatch


def test_knowledge_source_accepts_canonical_testing_metadata():
    approved_at = datetime.now(timezone.utc)
    value = KnowledgeSourceCreate(
        title="Đặc tả đăng nhập",
        content="Người dùng đăng nhập bằng email và mật khẩu",
        source_type="SRS",
        authority="APPROVED_SOURCE",
        owner_id="BA-01",
        module="Xác thực",
        component="Đăng nhập",
        product_area="Tài khoản",
        release_id="REL-01",
        external_source_id="JIRA-123",
        approval_status="APPROVED",
        approved_by="QA-LEAD-01",
        approved_at=approved_at,
        source_version="2.1",
        effective_from=approved_at,
        tags=["authentication", "release-2"],
    )
    assert value.source_type == "SRS"
    assert value.authority == "APPROVED_SOURCE"
    assert value.component == "Đăng nhập"


@pytest.mark.parametrize(
    "source_type",
    ["teacher_material", "official_textbook", "curriculum", "reference", "api_contract", "other"],
)
def test_knowledge_source_rejects_legacy_source_types(source_type):
    with pytest.raises(ValidationError):
        KnowledgeSourceCreate(title="Nguồn cũ", content="Nội dung", source_type=source_type)


@pytest.mark.parametrize("authority", ["teacher", "official", "supplemental", "reference"])
def test_knowledge_source_rejects_legacy_authorities(authority):
    with pytest.raises(ValidationError):
        KnowledgeSourceCreate(title="Nguồn cũ", content="Nội dung", authority=authority)


def test_approved_knowledge_source_requires_approval_provenance():
    with pytest.raises(ValidationError):
        KnowledgeSourceCreate(
            title="Nguồn chưa đủ provenance",
            content="Nội dung",
            approval_status="APPROVED",
        )


def test_requirement_document_patch_exposes_complete_v5_metadata():
    fields = RequirementDocumentPatch.model_fields
    assert {
        "owner_id",
        "module",
        "component",
        "product_area",
        "release_id",
        "external_source_id",
        "approval_status",
        "approved_by",
        "approved_at",
        "source_version",
        "effective_from",
        "tags",
    } <= fields.keys()
    assert {"teacher_id", "subject", "grade"}.isdisjoint(fields)
