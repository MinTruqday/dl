import base64
import io
import os
from uuid import uuid4
import zipfile

import httpx


base_url = os.getenv("ASSESSMENT_TEST_URL", "http://assessment:8000")
run_id = uuid4().hex
headers = {"x-test-user-id": f"teacher-import-{run_id}", "x-test-user-role": "author"}


def docx_bytes():
    document = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
<w:p><w:r><w:t>Câu 1 Hai cộng hai bằng bao nhiêu</w:t></w:r></w:p>
<w:p><w:r><w:t>A 3</w:t></w:r></w:p>
<w:p><w:r><w:t>B 4</w:t></w:r></w:p>
</w:body></w:document>"""
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
    relationships = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("word/document.xml", document)
    return buffer.getvalue()


with httpx.Client(base_url=base_url, timeout=180) as client:
    draft_response = client.post(
        "/assessment-drafts",
        headers=headers,
        json={
            "title": f"Đề nhập tệp {run_id}",
            "context": {"education_level": "THPT", "subject": "math", "target_program": "grade_12"},
            "layout_doc": {"type": "doc", "content": []},
            "research_blind_mode": True,
        },
    )
    assert draft_response.status_code == 201, draft_response.text
    draft = draft_response.json()
    import_response = client.post(
        f"/assessment-drafts/{draft['_id']}/import-file",
        headers=headers,
        json={
            "idempotency_key": f"import-file-{run_id}",
            "file_name": "questions.docx",
            "data": base64.b64encode(docx_bytes()).decode(),
            "answer_key": {"1": "B"},
        },
    )
    assert import_response.status_code == 202, import_response.text
    job = import_response.json()
    assert job["parser_version"] == "docling_question_parser_v1"
    assert len(job["candidates"]) == 1
    assert job["candidates"][0]["source_page"] == 1
    assert job["candidates"][0]["answer_key"] == {"option_id": "B"}
    repeated = client.post(
        f"/assessment-drafts/{draft['_id']}/import-file",
        headers=headers,
        json={
            "idempotency_key": f"import-file-{run_id}",
            "file_name": "questions.docx",
            "data": base64.b64encode(docx_bytes()).decode(),
            "answer_key": {"1": "B"},
        },
    )
    assert repeated.status_code == 202, repeated.text
    assert repeated.json()["_id"] == job["_id"]

print("assessment file import integration passed")
