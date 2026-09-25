import csv
import io
import json
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from src.services.domain_policy import domain_policy


EXPORT_POLICY = domain_policy("status_report_export")


def display(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return str(value)


def report_rows(report):
    period = report.get("reporting_period") or {}
    basis = report.get("snapshot_basis") or {}
    metrics = basis.get("metrics") or {}
    rows = [
        ("Mã báo cáo", report.get("_id")),
        ("Dự án", report.get("project_id")),
        ("Kế hoạch kiểm thử", report.get("test_plan_id")),
        ("Phiên bản chiến lược", report.get("strategy_version_id")),
        ("Bản phát hành", report.get("release_id")),
        ("Bản dựng", report.get("build_id")),
        ("Kỳ báo cáo bắt đầu", report.get("reporting_period_start", period.get("start_at"))),
        ("Kỳ báo cáo kết thúc", report.get("reporting_period_end", period.get("end_at"))),
        ("Ảnh chụp", report.get("snapshot_id")),
        ("Dấu vân tay nguồn", report.get("snapshot_source_fingerprint")),
        ("Trạng thái", report.get("status")),
        ("Khuyến nghị", report.get("recommendation")),
        ("Tóm tắt điều hành", report.get("executive_summary")),
        ("Tóm tắt tiến độ", report.get("progress_summary")),
        ("Tóm tắt độ phủ", report.get("coverage_summary")),
        ("Tóm tắt lỗi", report.get("defect_summary")),
        ("Tóm tắt bảo trì", report.get("maintenance_summary")),
        ("Diễn giải rủi ro", report.get("risk_explanation")),
        ("Dự báo", report.get("forecast")),
        ("Diễn giải khuyến nghị", report.get("recommendation_narrative")),
        ("Tỷ lệ thực thi", metrics.get("execution_percent")),
        ("Tỷ lệ đạt", metrics.get("pass_rate")),
        ("Độ phủ yêu cầu", metrics.get("requirement_coverage")),
        ("Độ phủ điều kiện kiểm thử", metrics.get("test_condition_coverage")),
        ("Cổng chất lượng", basis.get("quality_gate_status")),
        ("Sai lệch", report.get("deviations", [])),
        ("Trở ngại", report.get("blockers", [])),
        ("Rủi ro", report.get("risks", [])),
        ("Hành động kiểm soát", report.get("control_actions", [])),
        ("Mã hành động kiểm soát", report.get("control_action_ids", [])),
        ("Phân phối", report.get("distribution", [])),
        ("Bằng chứng", report.get("evidence_refs", [])),
    ]
    return [(label, display(value)) for label, value in rows]


def export_csv(report):
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["Trường", "Giá trị"])
    writer.writerows(report_rows(report))
    return stream.getvalue().encode("utf-8-sig")


def export_docx(report):
    paragraphs = "".join(
        f'<w:p><w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">{escape(label)}: </w:t></w:r><w:r><w:t xml:space="preserve">{escape(value)}</w:t></w:r></w:p>'
        for label, value in report_rows(report)
    )
    document = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{paragraphs}<w:sectPr/></w:body></w:document>'
    content_types = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'
    relationships = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'
    stream = io.BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("word/document.xml", document)
    return stream.getvalue()


def export_pdf(report):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas

    font_name = EXPORT_POLICY["pdf_fallback_font"]
    font_path = EXPORT_POLICY["pdf_font_path"]
    try:
        pdfmetrics.registerFont(TTFont(EXPORT_POLICY["pdf_font_name"], font_path))
        font_name = EXPORT_POLICY["pdf_font_name"]
    except (OSError, ValueError):
        font_name = EXPORT_POLICY["pdf_fallback_font"]
    stream = io.BytesIO()
    page = canvas.Canvas(stream, pagesize=A4)
    width, height = A4
    margin = EXPORT_POLICY["pdf_margin"]
    y = height - margin
    page.setFont(font_name, EXPORT_POLICY["pdf_title_size"])
    page.drawString(margin, y, "Báo cáo trạng thái kiểm thử")
    y -= EXPORT_POLICY["pdf_title_gap"]
    page.setFont(font_name, EXPORT_POLICY["pdf_body_size"])
    for label, value in report_rows(report):
        text = f"{label}: {value}"
        while text:
            line = text[: EXPORT_POLICY["pdf_line_length"]]
            text = text[EXPORT_POLICY["pdf_line_length"] :]
            if y < margin:
                page.showPage()
                page.setFont(font_name, EXPORT_POLICY["pdf_body_size"])
                y = height - margin
            page.drawString(margin, y, line)
            y -= EXPORT_POLICY["pdf_line_height"]
    page.save()
    return stream.getvalue()


def export_status_report(report, format_name):
    exporters = dict(
        zip(EXPORT_POLICY["supported_formats"], (export_csv, export_docx, export_pdf))
    )
    if format_name not in exporters:
        raise ValueError(EXPORT_POLICY["unsupported_format_code"])
    return exporters[format_name](report)
