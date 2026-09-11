import csv
import io
import json
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


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
        ("Bản phát hành", report.get("release_id")),
        ("Bản dựng", report.get("build_id")),
        ("Kỳ báo cáo bắt đầu", period.get("start_at")),
        ("Kỳ báo cáo kết thúc", period.get("end_at")),
        ("Snapshot", report.get("snapshot_id")),
        ("Dấu vân tay nguồn", report.get("snapshot_source_fingerprint")),
        ("Trạng thái", report.get("status")),
        ("Khuyến nghị", report.get("recommendation")),
        ("Tóm tắt điều hành", report.get("executive_summary")),
        ("Tóm tắt tiến độ", report.get("progress_summary")),
        ("Tóm tắt độ phủ", report.get("coverage_summary")),
        ("Tóm tắt lỗi", report.get("defect_summary")),
        ("Dự báo", report.get("forecast")),
        ("Tỷ lệ thực thi", metrics.get("execution_percent")),
        ("Tỷ lệ đạt", metrics.get("pass_rate")),
        ("Độ phủ yêu cầu", metrics.get("requirement_coverage")),
        ("Độ phủ điều kiện kiểm thử", metrics.get("test_condition_coverage")),
        ("Quality gate", basis.get("quality_gate_status")),
        ("Sai lệch", report.get("deviations", [])),
        ("Blocker", report.get("blockers", [])),
        ("Rủi ro", report.get("risks", [])),
        ("Control action", report.get("control_actions", [])),
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

    font_name = "Helvetica"
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try:
        pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
        font_name = "DejaVuSans"
    except (OSError, ValueError):
        pass
    stream = io.BytesIO()
    page = canvas.Canvas(stream, pagesize=A4)
    width, height = A4
    y = height - 42
    page.setFont(font_name, 13)
    page.drawString(42, y, "Báo cáo trạng thái kiểm thử")
    y -= 28
    page.setFont(font_name, 8)
    for label, value in report_rows(report):
        text = f"{label}: {value}"
        while text:
            line = text[:120]
            text = text[120:]
            if y < 42:
                page.showPage()
                page.setFont(font_name, 8)
                y = height - 42
            page.drawString(42, y, line)
            y -= 12
    page.save()
    return stream.getvalue()


def export_status_report(report, format_name):
    exporters = {"csv": export_csv, "docx": export_docx, "pdf": export_pdf}
    if format_name not in exporters:
        raise ValueError("STATUS_REPORT_EXPORT_FORMAT_UNSUPPORTED")
    return exporters[format_name](report)
