from io import BytesIO
from zipfile import ZipFile

import pytest
from pydantic import ValidationError
from pypdf import PdfReader

from src.core.auth import ProjectRole, permissions_for_role
from src.domain.test_status_report import ReportingPeriod, TestStatusReportGenerate as StatusReportGenerate, status_report_hash
from src.services.test_status_report_export import export_csv, export_docx, export_pdf, report_rows
from src.services.test_status_report import default_recommendation, generated_summaries


def report_fixture():
    return {
        "_id": "TSR-1",
        "project_id": "PRJ-1",
        "test_plan_id": "TPLAN-1",
        "release_id": "REL-1",
        "build_id": "BLD-1",
        "reporting_period": {"start_at": "2026-09-01T00:00:00Z", "end_at": "2026-09-07T23:59:59Z"},
        "snapshot_id": "MONS-1",
        "snapshot_source_fingerprint": "a" * 64,
        "snapshot_basis": {"metrics": {"execution_percent": 95, "pass_rate": 90}, "quality_gate_status": "PASS"},
        "executive_summary": "Báo cáo kiểm thử tuần",
        "progress_summary": "Đã thực thi 95 phần trăm",
        "coverage_summary": "Độ phủ yêu cầu 100 phần trăm",
        "defect_summary": "Không còn lỗi blocker",
        "deviations": [],
        "blockers": [],
        "risks": ["Rủi ro còn lại"],
        "control_actions": [],
        "forecast": "Hoàn tất đúng kế hoạch",
        "recommendation": "ON_TRACK",
        "distribution": ["qa@example.com"],
        "evidence_refs": ["ATT-1"],
        "status": "APPROVED",
        "revision": 4,
    }


def test_reporting_period_and_generate_contract():
    value = StatusReportGenerate(
        snapshot_id="MONS-1",
        build_id="BLD-1",
        reporting_period={"start_at": "2026-09-01T00:00:00Z", "end_at": "2026-09-07T00:00:00Z"},
        recommendation="READY_WITH_RISK",
    )
    assert value.recommendation == "READY_WITH_RISK"
    with pytest.raises(ValidationError):
        ReportingPeriod(start_at="2026-09-08T00:00:00Z", end_at="2026-09-07T00:00:00Z")
    with pytest.raises(ValidationError):
        StatusReportGenerate(snapshot_id="MONS-1", reporting_period={"start_at": "2026-09-01T00:00:00Z", "end_at": "2026-09-07T00:00:00Z"})


def test_status_report_hash_tracks_content_not_workflow_metadata():
    report = report_fixture()
    initial = status_report_hash(report)
    report.update({"status": "PUBLISHED", "revision": 9, "approved_by": "QA-1"})
    assert status_report_hash(report) == initial
    report["forecast"] = "Trễ một ngày"
    assert status_report_hash(report) != initial


def test_status_report_generation_summary_and_recommendation_are_deterministic():
    snapshot = {
        "metrics": {
            "executed_test_count": 19,
            "planned_test_count": 20,
            "execution_percent": 95,
            "requirement_coverage": 100,
            "test_condition_coverage": 90,
            "risk_coverage": 80,
            "open_blocker": 0,
            "open_critical": 1,
            "reopened": 2,
        },
        "effective_quality_gate_status": "FAIL",
        "blockers": [],
    }
    assert generated_summaries(snapshot) == generated_summaries(snapshot)
    assert default_recommendation(snapshot) == "NOT_READY"
    snapshot["blockers"] = ["Dừng phát hành"]
    assert default_recommendation(snapshot) == "BLOCKED"


def test_status_report_exports_preserve_point_in_time_content():
    report = report_fixture()
    assert any(label == "Dấu vân tay nguồn" and value == "a" * 64 for label, value in report_rows(report))
    csv_data = export_csv(report)
    assert "Báo cáo kiểm thử tuần" in csv_data.decode("utf-8-sig")
    docx_data = export_docx(report)
    with ZipFile(BytesIO(docx_data)) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
    assert "Báo cáo kiểm thử tuần" in document
    pdf_data = export_pdf(report)
    assert pdf_data.startswith(b"%PDF")
    assert len(PdfReader(BytesIO(pdf_data)).pages) >= 1


def test_status_report_permissions_keep_final_approval_with_qa_lead():
    lead = permissions_for_role(ProjectRole.QA_LEAD)
    tester = permissions_for_role(ProjectRole.TESTER)
    analyst = permissions_for_role(ProjectRole.BA)
    viewer = permissions_for_role(ProjectRole.VIEWER)
    assert {"teststatusreport.read", "teststatusreport.create", "teststatusreport.update", "teststatusreport.review", "teststatusreport.approve", "teststatusreport.export"} <= lead
    assert {"teststatusreport.read", "teststatusreport.create", "teststatusreport.update", "teststatusreport.review", "teststatusreport.export"} <= tester
    assert "teststatusreport.approve" not in tester | analyst | viewer
    assert "teststatusreport.read" in analyst & viewer
